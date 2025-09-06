from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.deps import current_user
from app.db.session import get_db
from app.services.categories import list_categories, create_category, delete_category, update_category_name
from app.templates import render
from app.models.category import Category


router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_class=HTMLResponse)
async def page_me(request:Request, user=Depends(current_user), db: Session = Depends(get_db)):
    cats = list_categories(db, user_id=user["id"])
    return render(request, "categories/index.html", {"categories": cats})

@router.post("/create", response_class=HTMLResponse)
async def add(request:Request, name: str = Form(...), user=Depends(current_user), db: Session = Depends(get_db)):
    create_category(db, user_id=user["id"], name=name)
    cats = list_categories(db, user_id=user["id"])
    return render(request, "categories/_list.html", {"categories": cats})

@router.post("/delete/{category_id}")
async def remove(request:Request, category_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    delete_category(db, user_id=user["id"], category_id=category_id)
    cats = list_categories(db, user_id=user["id"])
    return render(request, "categories/_list.html", {"categories": cats})

@router.get("/item/{category_id}", response_class=HTMLResponse)
async def item_view(request: Request, category_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.user_id == user["id"], Category.id == category_id).first()
    return render(request, "categories/_item.html", {"c": c})

@router.get("/edit/{category_id}", response_class=HTMLResponse)
async def item_edit(request: Request, category_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.user_id == user["id"], Category.id == category_id).first()
    return render(request, "categories/_item_edit.html", {"c": c})

@router.post("/update/{category_id}", response_class=HTMLResponse)
async def item_update(
    request: Request,
    category_id: int,
    name: str = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    update_category_name(db, user_id=user["id"], category_id=category_id, new_name=name)
    # return the display state for just this item
    c = db.query(Category).filter(Category.user_id == user["id"], Category.id == category_id).first()
    return render(request, "categories/_item.html", {"c": c})