import logging
import pandas as pd

from datetime import datetime
from typing import List

from io import StringIO

from sqlalchemy import select, asc, desc, func
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from rdp.api.api_types import ValuesWithCount

from .model import Base, Value, ValueType, Device, Room, RoomGroup


class Crud:
    def __init__(self, engine):
        self._engine = engine
        self.IntegrityError = IntegrityError
        self.NoResultFound = NoResultFound

        Base.metadata.create_all(self._engine)

    def add_or_update_value_type(
        self,
        value_type_id: int = None,
        value_type_name: str = None,
        value_type_unit: str = None,
    ) -> None:
        """update or add a value type

        Args:
            value_type_id (int, optional): ValueType id to be modified (if None a new ValueType is added), Default to None.
            value_type_name (str, optional): Typename wich should be set or updated. Defaults to None.
            value_type_unit (str, optional): Unit of mesarument wich should be set or updated. Defaults to None.

        Returns:
            _type_: _description_
        """
        with Session(self._engine) as session:
            stmt = select(ValueType).where(ValueType.id == value_type_id)
            db_type = None
            for type in session.scalars(stmt):
                db_type = type
            if db_type is None:
                db_type = ValueType(id=value_type_id)
            if value_type_name:
                db_type.type_name = value_type_name
            elif not db_type.type_name:
                db_type.type_name = "TYPE_%d" % value_type_id
            if value_type_unit:
                db_type.type_unit = value_type_unit
            elif not db_type.type_unit:
                db_type.type_unit = "UNIT_%d" % value_type_id
            session.add_all([db_type])
            session.commit()
            return db_type

    def add_value(
        self, value_time: int, value_type: int, device: int, value_value: float
    ) -> None:
        """Add a measurement point to the database.

        Args:
            value_time (int): unix time stamp of the value.
            value_type (int): Valuetype id of the given value.
            value_value (float): The measurement value as float.
        """
        with Session(self._engine) as session:
            stmt = select(ValueType).where(ValueType.id == value_type)
            db_type = self.add_or_update_value_type(value_type)
            db_value = Value(
                time=value_time, value=value_value, value_type=db_type, device_id=device
            )

            session.add_all([db_type, db_value])
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise

    def add_or_update_device(
        self,
        device_id: int = None,
        device_device: str = None,
        device_name: str = None,
        room_id: int = None,
    ) -> Device:
        """Update or add a device

        Args:
            device_id (int, optional): Device id to be modified (if None a new Device is added), Default to None.
            device_device (str, optional): Device path where sensor data is coming from. Defaults to None.
            device_name (str, optional): Device name. Defaults to None.

        Returns:
            Device: The added or updated device
        """
        db_device = None
        with Session(self._engine) as session:
            db_device = None
            if device_id is not None:
                stmt = select(Device).where(Device.id == device_id)
                for device in session.scalars(stmt):
                    db_device = device
                if db_device is None:
                    logging.error(f"Device with id:{device_id} does not exist.")
                    raise NoResultFound()
            if db_device is None:
                db_device = Device()
            if device_device:
                db_device.device = device_device
            if device_name:
                db_device.name = device_name
            if room_id:
                db_device.room_id = room_id
            session.add(db_device)
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise
            session.refresh(db_device)
        return db_device

    def delete_device(
        self,
        device_id: int,
    ) -> Device:
        """Delete a device

        Args:
            device_id (int): Device id to be deleted.

        Returns:
            Device: The deleted device
        """
        db_device = None
        with Session(self._engine) as session:
            stmt = select(Device).where(Device.id == device_id)
            for device in session.scalars(stmt):
                db_device = device
            if db_device is None:
                logging.error(f"Device with id:{device_id} does not exist.")
                raise NoResultFound()
            session.delete(db_device)
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise
        return db_device

    def add_or_update_room(
        self, room_id: int = None, room_name: str = None, room_group_id: int = None
    ) -> Room:
        """Update or add a Room

        Args:
            room_id (int, optional): Room id to be modified (if None a new Room is added), Default to None.
            room_name (str, optional): Room name. Defaults to None.

        Returns:
            Room: The added or updated room
        """
        db_room = None
        with Session(self._engine) as session:
            if room_id is not None:
                stmt = select(Room).where(Room.id == room_id)
                for room in session.scalars(stmt):
                    db_room = room
                if db_room is None:
                    logging.error(f"Room with id:{room_id} does not exist.")
                    raise NoResultFound()
            if db_room is None:
                db_room = Room()
            if room_name:
                db_room.name = room_name
            db_room.room_group_id = room_group_id
            session.add(db_room)
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise
            session.refresh(db_room)
        return db_room

    def add_or_update_room_group(
        self,
        room_group_id: int = None,
        room_group_name: str = None,
        parent_group_id: int = None,
    ) -> Room:
        db_room_group = None
        with Session(self._engine) as session:
            if room_group_id is not None:
                stmt = select(RoomGroup).where(RoomGroup.id == room_group_id)
                for room_group in session.scalars(stmt):
                    db_room_group = room_group
                if db_room_group is None:
                    logging.error(f"Room with id:{room_group_id} does not exist.")
                    raise NoResultFound()
            if db_room_group is None:
                db_room_group = RoomGroup()
            if room_group_name:
                db_room_group.name = room_group_name
            if parent_group_id:
                db_room_group.room_group_id = parent_group_id
            session.add(db_room_group)
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise
            session.refresh(db_room_group)
        return db_room_group

    def delete_room_group(
        self,
        room_group_id: int = None,
    ) -> Room:
        db_room_group = None
        with Session(self._engine) as session:
            stmt = select(RoomGroup).where(RoomGroup.id == room_group_id)
            for room_group in session.scalars(stmt):
                db_room_group = room_group
            if db_room_group is None:
                logging.error(f"Room with id:{room_group_id} does not exist.")
                raise NoResultFound()
            session.delete(db_room_group)
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise
        return db_room_group

    def delete_room(
        self,
        room_id: int,
    ) -> Room:
        """Delete a room

        Args:
            room_id (int): Room id to be deleted.

        Returns:
            Room: The deleted room
        """
        db_room = None
        with Session(self._engine) as session:
            stmt = select(Room).where(Room.id == room_id)
            for room in session.scalars(stmt):
                db_room = room
            if db_room is None:
                logging.error(f"Room with id:{room_id} does not exist.")
                raise NoResultFound()
            session.delete(db_room)
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity")
                raise
        return db_room

    def get_value_types(self) -> List[ValueType]:
        """Get all configured value types

        Returns:
            List[ValueType]: List of ValueType objects.
        """
        with Session(self._engine) as session:
            stmt = select(ValueType)
            return session.scalars(stmt).all()

    def get_value_type(self, value_type_id: int) -> ValueType:
        """Get a special ValueType

        Args:
            value_type_id (int): the primary key of the ValueType

        Returns:
            ValueType: The ValueType object
        """
        with Session(self._engine) as session:
            stmt = select(ValueType).where(ValueType.id == value_type_id)
            return session.scalars(stmt).one()

    def get_values(
        self,
        value_type_id: int = None,
        start: int = None,
        end: int = None,
        device_id: int = None,
        page: int = None,
        order: str = None,
        isasc: str = None,
    ) -> ValuesWithCount:
        """Get Values from database.

        The result can be filtered by the following paramater:

        Args:
            value_type_id (int, optional): If set, only value of this given type will be returned. Defaults to None.
            start (int, optional): If set, only values with a timestamp as least as big as start are returned. Defaults to None.
            end (int, optional): If set, only values with a timestamp as most as big as end are returned. Defaults to None.

        Returns:
            List[Value]: _description_
        """
        with Session(self._engine) as session:
            stmt = select(Value)
            order_dir = asc if isasc == "true" else desc
            if value_type_id is not None:
                stmt = stmt.join(Value.value_type).where(ValueType.id == value_type_id)
            if start is not None:
                stmt = stmt.where(Value.time >= start)
            if end is not None:
                stmt = stmt.where(Value.time <= end)
            if device_id is not None:
                stmt = stmt.where(Value.device_id == device_id)
            if order == "type":
                stmt = stmt.join(Value.value_type).order_by(
                    order_dir(ValueType.type_name)
                )
            if order == "value":
                stmt = stmt.order_by(order_dir(Value.value))
            if order == "device":
                stmt = stmt.join(Value.device).order_by(order_dir(Device.name))
            else:
                stmt = stmt.order_by(order_dir(Value.time))

            count = session.query(func.count()).select_from(stmt.subquery()).scalar()

            if page is None:
                page = 1
            stmt = stmt.offset(10 * (page - 1)).limit(10)

            logging.error(start)
            logging.error(stmt)

            values_with_count = {
                "count": count,
                "values": session.scalars(stmt).all(),
            }

            return values_with_count

    def get_values_average(
        self,
        value_type_id: int = None,
        start: int = None,
        end: int = None,
        device_id: int = None,
    ) -> float:
        """Get Values from database.

        The result can be filtered by the following paramater:

        Args:
            value_type_id (int, optional): If set, only value of this given type will be returned. Defaults to None.
            start (int, optional): If set, only values with a timestamp as least as big as start are returned. Defaults to None.
            end (int, optional): If set, only values with a timestamp as most as big as end are returned. Defaults to None.

        Returns:
            List[Value]: _description_
        """
        with Session(self._engine) as session:
            stmt = select(func.avg(Value.value).label("avg"))
            if value_type_id is not None:
                stmt = stmt.join(Value.value_type).where(ValueType.id == value_type_id)
            if start is not None:
                stmt = stmt.where(Value.time >= start)
            if end is not None:
                stmt = stmt.where(Value.time <= end)
            if device_id is not None:
                stmt = stmt.where(Value.device_id == device_id)
            logging.error(start)
            logging.error(stmt)

            return session.scalars(stmt).all()[0]

    def get_device(self, id: int) -> Device:
        """Get Device from database.

        Args:
            id (int): device id

        Returns:
            Device
        """
        with Session(self._engine) as session:
            stmt = select(Device).where(Device.id == id)
            return session.scalars(stmt).one()

    def get_devices(self) -> List[Device]:
        """Get Devices from database.

        Returns:
            List[Device]
        """
        with Session(self._engine) as session:
            stmt = select(Device)
            return session.scalars(stmt).all()

    def get_rooms(self, room_group_id: int = None):
        with Session(self._engine) as session:
            stmt = select(Room)
            if room_group_id:
                stmt = stmt.where(RoomGroup.room_group_id == room_group_id)
            return session.scalars(stmt).all()

    def get_room(self, id: int) -> Room:
        """Get Room from database.

        Args:
            id (int): room id

        Returns:
            Room
        """
        with Session(self._engine) as session:
            stmt = select(Room).where(Room.id == id)
            return session.scalars(stmt).one()

    def get_room_groups(self):
        with Session(self._engine) as session:
            stmt = select(RoomGroup)
            return session.scalars(stmt).all()

    def get_room_group(self, id: int):
        with Session(self._engine) as session:
            stmt = select(RoomGroup).where(RoomGroup.id == id)
            return session.scalars(stmt).one()

    def load_csv(self, csv_text: str, device_id: int):
        """Insert data from csv to the database.

        Returns:
            None
        """
        df = pd.read_csv(StringIO(csv_text.decode("utf-8")))
        df_no_time = df.drop(columns=["time"])
        no_time_keys = df_no_time.keys()
        with Session(self._engine) as session:
            device = session.query(Device).filter(Device.id == device_id).one()
            for _, row in df.iterrows():
                for key in no_time_keys:
                    value_type = (
                        session.query(ValueType)
                        .filter(ValueType.type_name == key)
                        .one()
                    )
                    time = datetime.fromisoformat(row["time"]).timestamp()
                    value = Value(
                        time=time, value=row[key], value_type=value_type, device=device
                    )
                    session.add(value)
            session.commit()
