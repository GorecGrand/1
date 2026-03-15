"""SQLAlchemy models for the agent service domain."""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)

    vehicle = relationship("Vehicle", back_populates="driver", uselist=False)
    orders = relationship("Order", back_populates="driver")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Driver id={self.id} name={self.name!r}>"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String, nullable=False, unique=True)
    model = Column(String, nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), unique=True)

    driver = relationship("Driver", back_populates="vehicle")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Vehicle id={self.id} plate={self.license_plate!r}>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    pickup_location = Column(String, nullable=False)
    dropoff_location = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    driver = relationship("Driver", back_populates="orders")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Order id={self.id} customer={self.customer_name!r}>"
