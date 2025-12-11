from typing import Optional
from app.database import get_master_db
from app.utils.security import hash_password, ensure_bcrypt_compatible_password
from app.utils.validators import validate_password_strength
from app.errors import BadRequest, NotFound, Conflict, Forbidden, InternalError
from datetime import datetime
from pymongo.errors import DuplicateKeyError, OperationFailure
from motor.motor_asyncio import AsyncIOMotorCollection


class OrganizationService:
    def __init__(self, db=None):
        self.db = db or get_master_db()
        self.orgs = self.db.organizations
        self.admins = self.db.admins

    async def create_organization(self, organization_name: str, email: str, password: str) -> dict:
        # ensure unique organization_name and admin email
        if await self.orgs.find_one({"organization_name": organization_name}):
            raise Conflict("organization already exists")
        if await self.admins.find_one({"email": email}):
            raise Conflict("admin email already in use")

        collection_name = f"org_{organization_name}"
        # create empty collection if not exists
        existing_collections = await self.db.list_collection_names()
        if collection_name not in existing_collections:
            try:
                await self.db.create_collection(collection_name)
            except Exception:
                pass

        if not validate_password_strength(password):
            raise BadRequest("password does not meet strength requirements")
        # ensure bcrypt length limits are enforced with a clear error
        try:
            ensure_bcrypt_compatible_password(password)
        except ValueError as e:
            raise BadRequest(str(e))
        hashed = hash_password(password)
        admin_doc = {
            "email": email,
            "password": hashed,
            "organization_name": organization_name,
            "created_at": datetime.utcnow()
        }
        try:
            res = await self.admins.insert_one(admin_doc)
        except DuplicateKeyError:
            raise Conflict("admin email already in use")
        admin_id = res.inserted_id

        org_doc = {
            "organization_name": organization_name,
            "collection_name": collection_name,
            "admin_id": admin_id,
            "created_at": datetime.utcnow()
        }
        try:
            await self.orgs.insert_one(org_doc)
        except DuplicateKeyError:
            # cleanup admin if org insert failed
            await self.admins.delete_one({"_id": admin_id})
            raise Conflict("organization already exists")

        return {
            "organization_name": organization_name,
            "collection_name": collection_name,
            "admin_email": email,
            "created_at": org_doc["created_at"]
        }

    async def get_organization(self, organization_name: str) -> Optional[dict]:
        org = await self.orgs.find_one({"organization_name": organization_name})
        if not org:
            return None
        admin = await self.admins.find_one({"_id": org.get("admin_id")})
        return {
            "organization_name": org.get("organization_name"),
            "collection_name": org.get("collection_name"),
            "admin_email": admin.get("email") if admin else None,
            "created_at": org.get("created_at")
        }

    async def update_organization(self, organization_name: str, new_organization_name: Optional[str] = None,
                                  email: Optional[str] = None, password: Optional[str] = None) -> dict:
        org = await self.orgs.find_one({"organization_name": organization_name})
        if not org:
            raise NotFound("organization does not exist")

        updates = {}
        if new_organization_name:
            # ensure new name not used
            if await self.orgs.find_one({"organization_name": new_organization_name}):
                raise Conflict("new organization name already exists")

            old_collection = org.get("collection_name")
            new_collection = f"org_{new_organization_name}"

            # Prefer a rename which preserves _id and indexes. If rename is not possible, fall back to copy.
            try:
                # ensure old collection exists
                existing = await self.db.list_collection_names()
                if old_collection not in existing:
                    await self.db.create_collection(new_collection)
                else:
                    col: AsyncIOMotorCollection = self.db[old_collection]
                    await col.rename(new_collection)
            except OperationFailure:
                old_col = self.db[old_collection]
                new_col = self.db[new_collection]
                cursor = old_col.find({})
                docs = []
                async for d in cursor:
                    docs.append(d)
                if docs:
                    try:
                        await new_col.insert_many(docs)
                    except DuplicateKeyError:
                        for d in docs:
                            d.pop("_id", None)
                        await new_col.insert_many(docs)
                await old_col.drop()

            updates["collection_name"] = new_collection
            updates["organization_name"] = new_organization_name

            # update admin reference(s)
            await self.admins.update_many({"organization_name": organization_name}, {"$set": {"organization_name": new_organization_name}})

        if email or password:
            admin_id = org.get("admin_id")
            set_fields = {}
            if email:
                set_fields["email"] = email
            if password:
                if not validate_password_strength(password):
                    raise BadRequest("password does not meet strength requirements")
                try:
                    ensure_bcrypt_compatible_password(password)
                except ValueError as e:
                    raise BadRequest(str(e))
                set_fields["password"] = hash_password(password)
            if set_fields:
                await self.admins.update_one({"_id": admin_id}, {"$set": set_fields})

        if updates:
            try:
                await self.orgs.update_one({"_id": org.get("_id")}, {"$set": updates})
            except Exception:
                raise InternalError("failed to update organization metadata")

        new_name = new_organization_name or organization_name
        return await self.get_organization(new_name)

    async def delete_organization(self, organization_name: str, requesting_admin_email: str):
        org = await self.orgs.find_one({"organization_name": organization_name})
        if not org:
            raise NotFound("organization does not exist")
        admin = await self.admins.find_one({"_id": org.get("admin_id")})
        if not admin or admin.get("email") != requesting_admin_email:
            raise Forbidden("only the org admin can delete the organization")

        collection_name = org.get("collection_name")
        try:
            await self.db[collection_name].drop()
        except Exception:
            pass

        await self.admins.delete_many({"organization_name": organization_name})
        await self.orgs.delete_one({"_id": org.get("_id")})

        return {"deleted": True, "organization_name": organization_name}
