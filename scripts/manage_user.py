"""Manage user status and priority"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from config import get_settings  # Add this import

settings = get_settings()  # Add this line

async def get_user(user_id: int):
    """Get user details"""
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"\n📊 User: {user.first_name} (ID: {user.id})")
            print(f"   Status: {'✅ Active' if user.is_active else '❌ Inactive'}")
            print(f"   Priority: {user.priority} {'⚡' if user.priority <= 2 else ''}")
            print(f"   Strikes: {user.strikes}/{settings.max_strikes} {'⚠️' if user.strikes > 0 else '✅'}")
            print(f"   Username: @{user.username if user.username else 'N/A'}")
        else:
            print(f"❌ User {user_id} not found")
        
        return user

async def set_user_status(user_id: int, is_active: bool):
    """Activate or deactivate user"""
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.is_active = is_active
            await db.commit()
            status = "activated" if is_active else "deactivated"
            print(f"✅ User {user.first_name} (ID: {user_id}) has been {status}")
        else:
            print(f"❌ User {user_id} not found")

async def set_user_priority(user_id: int, priority: int):
    """Set user priority (1-10, where 1 is highest)"""
    if not 1 <= priority <= 10:
        print("❌ Priority must be between 1 and 10")
        return
    
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.priority = priority
            await db.commit()
            print(f"✅ User {user.first_name} (ID: {user_id}) priority set to {priority}")
        else:
            print(f"❌ User {user_id} not found")

async def reset_strikes(user_id: int):
    """Reset user strikes to 0"""
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            old_strikes = user.strikes
            user.strikes = 0
            await db.commit()
            print(f"✅ User {user.first_name} (ID: {user_id}) strikes reset from {old_strikes} to 0")
        else:
            print(f"❌ User {user_id} not found")

async def list_users():
    """List all users"""
    async with AsyncSessionLocal() as db:
        stmt = select(User).order_by(User.priority, User.id)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        print(f"\n📋 Total Users: {len(users)}\n")
        for user in users:
            status = "✅" if user.is_active else "❌"
            priority_icon = "⚡" if user.priority <= 2 else ""
            strikes_icon = "⚠️" if user.strikes > 0 else ""
            strike_text = f" ({user.strikes} strikes)" if user.strikes > 0 else ""
            print(f"{status} {user.first_name} (ID: {user.id}) - Priority: {user.priority} {priority_icon}{strike_text}{strikes_icon}")

async def main():
    """Main menu"""
    if len(sys.argv) < 2:
        print("""
Usage:
  python scripts/manage_user.py list
  python scripts/manage_user.py get <user_id>
  python scripts/manage_user.py activate <user_id>
  python scripts/manage_user.py deactivate <user_id>
  python scripts/manage_user.py priority <user_id> <1-10>
  python scripts/manage_user.py reset-strikes <user_id>
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        await list_users()
    elif command == "get" and len(sys.argv) >= 3:
        await get_user(int(sys.argv[2]))
    elif command == "activate" and len(sys.argv) >= 3:
        await set_user_status(int(sys.argv[2]), True)
    elif command == "deactivate" and len(sys.argv) >= 3:
        await set_user_status(int(sys.argv[2]), False)
    elif command == "priority" and len(sys.argv) >= 4:
        await set_user_priority(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "reset-strikes" and len(sys.argv) >= 3:
        await reset_strikes(int(sys.argv[2]))
    else:
        print("❌ Invalid command")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())