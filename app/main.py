"""FastAPI application entrypoint for the agent service backend."""

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from .db import engine, get_db, session_scope
from .models import Base, Driver, Order, Vehicle
from .schemas import DriverRead, OrderCreate, OrderRead


app = FastAPI(
    title="Agent Service Backend",
    description="Sample FastAPI service agent template.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables and seed demo data."""
    Base.metadata.create_all(bind=engine)
    _seed_demo_data()


def _seed_demo_data() -> None:
    with session_scope() as db:
        if db.query(Driver).first():
            return

        driver_1 = Driver(name="John Doe", phone="+15550000001")
        driver_2 = Driver(name="Jane Smith", phone="+15550000002")

        vehicle_1 = Vehicle(license_plate="ABC123", model="Toyota Prius", driver=driver_1)
        vehicle_2 = Vehicle(license_plate="XYZ987", model="Hyundai Ioniq", driver=driver_2)

        db.add_all([driver_1, driver_2, vehicle_1, vehicle_2])


@app.post("/orders/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)) -> Order:
    """Create a new order and optionally assign a driver."""
    if order.driver_id is not None:
        driver = db.query(Driver).filter(Driver.id == order.driver_id).first()
        if driver is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    db_order = Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@app.get("/orders/", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)) -> list[Order]:
    """Return all orders."""
    return (
        db.query(Order)
        .options(selectinload(Order.driver).selectinload(Driver.vehicle))
        .all()
    )


@app.get("/drivers/", response_model=list[DriverRead])
def get_drivers(db: Session = Depends(get_db)) -> list[Driver]:
    """Return all registered drivers."""
    return db.query(Driver).options(selectinload(Driver.vehicle)).all()
