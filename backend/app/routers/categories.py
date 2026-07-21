from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.database.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.routers.deps import get_current_user
from app.services.cache import cache_service

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all categories for the user, including global system categories.
    """
    cache_key = f"user:{current_user.id}:categories"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    stmt = select(Category).where(
        or_(
            Category.user_id == current_user.id,
            Category.user_id.is_(None)
        )
    )
    result = db.execute(stmt).scalars().all()
    cache_service.set(cache_key, result, ttl=300)
    return result

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a custom category for the authenticated user.
    """
    # Check duplicate
    stmt = select(Category).where(
        Category.name.ilike(category_in.name),
        or_(
            Category.user_id == current_user.id,
            Category.user_id.is_(None)
        )
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category_in.name}' already exists."
        )

    category = Category(
        user_id=current_user.id,
        name=category_in.name,
        type=category_in.type,
        icon=category_in.icon,
        color=category_in.color
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    cache_service.delete(f"user:{current_user.id}:categories")
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a custom category. (System categories cannot be modified).
    """
    stmt = select(Category).where(Category.id == category_id)
    category = db.execute(stmt).scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
    
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update default system categories."
        )

    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
        
    db.commit()
    db.refresh(category)
    cache_service.delete(f"user:{current_user.id}:categories")
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a custom category. (System categories cannot be deleted).
    """
    stmt = select(Category).where(Category.id == category_id)
    category = db.execute(stmt).scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
    
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete default system categories."
        )
    
    db.delete(category)
    db.commit()
    cache_service.delete(f"user:{current_user.id}:categories")
    return

@router.post("/seed", response_model=List[CategoryResponse], status_code=status.HTTP_201_CREATED)
def seed_default_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Seed a user with default standard categories if they don't already have them.
    """
    defaults = [
        # Income categories
        {"name": "Salary", "type": "income", "icon": "Briefcase", "color": "#10B981"},
        {"name": "Freelance", "type": "income", "icon": "Laptop", "color": "#3B82F6"},
        {"name": "Investments", "type": "income", "icon": "TrendingUp", "color": "#8B5CF6"},
        
        # Expense categories
        {"name": "Food & Dining", "type": "expense", "icon": "Utensils", "color": "#EF4444"},
        {"name": "Housing & Rent", "type": "expense", "icon": "Home", "color": "#F59E0B"},
        {"name": "Transportation", "type": "expense", "icon": "Car", "color": "#06B6D4"},
        {"name": "Entertainment", "type": "expense", "icon": "Film", "color": "#EC4899"},
        {"name": "Utilities", "type": "expense", "icon": "Zap", "color": "#14B8A6"},
        {"name": "Shopping", "type": "expense", "icon": "ShoppingBag", "color": "#6366F1"},
        {"name": "Healthcare", "type": "expense", "icon": "HeartPulse", "color": "#F43F5E"},
    ]
    
    added_categories = []
    for item in defaults:
        stmt = select(Category).where(
            Category.name == item["name"],
            Category.user_id == current_user.id
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            cat = Category(
                user_id=current_user.id,
                name=item["name"],
                type=item["type"],
                icon=item["icon"],
                color=item["color"]
            )
            db.add(cat)
            added_categories.append(cat)
            
    if added_categories:
        db.commit()
        for cat in added_categories:
            db.refresh(cat)
        cache_service.delete(f"user:{current_user.id}:categories")
            
    # Also fetch all user-owned categories to return
    stmt = select(Category).where(Category.user_id == current_user.id)
    return db.execute(stmt).scalars().all()
