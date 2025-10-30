"""Pydantic schemas for request and response payloads."""

from typing import Optional

from pydantic import BaseModel


class VehicleBase(BaseModel):
    license_plate: str
    model: str


class VehicleRead(VehicleBase):
    id: int

    class Config:
        orm_mode = True


class DriverBase(BaseModel):
    name: str
    phone: str


class DriverRead(DriverBase):
    id: int
    vehicle: Optional[VehicleRead]

    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    pickup_location: str
    dropoff_location: str
    customer_name: str
    driver_id: Optional[int] = None


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: int
    driver: Optional[DriverRead]

    class Config:
        orm_mode = True
