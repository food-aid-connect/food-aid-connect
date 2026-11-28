"""Shared validation for the batch creation form and API documentation."""
from datetime import date
from decimal import Decimal as DecimalValue

from apiflask import Schema
from apiflask.fields import Date, Decimal, String, Time
from apiflask.validators import Length, OneOf, Range
from marshmallow import ValidationError, validates, validates_schema


CATEGORIES = (
    "Bread and bakery", "Fruit and vegetables", "Canned and dry goods",
    "Dairy", "Prepared meals", "Other",
)


class BatchDetailsSchema(Schema):
    category = String(allow_none=True, load_default=None, validate=OneOf(CATEGORIES))
    quantity_kg = Decimal(allow_none=True, load_default=None, places=3,
                          metadata={'minimum': 0.001, 'maximum': 9999999.999},
                          validate=Range(min=DecimalValue('0.001'),
                                         max=DecimalValue('9999999.999')))
    use_by_date = Date(allow_none=True, load_default=None)
    pickup_address = String(allow_none=True, load_default=None, validate=Length(max=255))
    pickup_start = Time(allow_none=True, load_default=None, metadata={'format': 'time'})
    pickup_end = Time(allow_none=True, load_default=None, metadata={'format': 'time'})

    @validates('use_by_date')
    def validate_use_by_date(self, value, **kwargs):
        if value is not None and value < date.today():
            raise ValidationError('Use-by date cannot be earlier than today.')

    @validates_schema
    def validate_pickup_window(self, data, **kwargs):
        start, end = data.get('pickup_start'), data.get('pickup_end')
        if any(value is not None and value.tzinfo is not None for value in (start, end)):
            raise ValidationError('Use local pickup times without a timezone.')
        if start is not None and end is not None:
            if end <= start:
                raise ValidationError('Pickup end must be later than pickup start.')


class BatchCreateSchema(BatchDetailsSchema):
    # New submissions require these; stored legacy records may still be null.
    quantity_kg = Decimal(required=True, places=3,
                          metadata={'minimum': 0.001, 'maximum': 9999999.999},
                          validate=Range(min=DecimalValue('0.001'),
                                         max=DecimalValue('9999999.999')))
    use_by_date = Date(required=True)
    title = String(required=True, validate=Length(min=1, max=120))
    pickup_date = Date(required=True)

    @validates_schema
    def validate_pickup_date(self, data, **kwargs):
        if data['pickup_date'] > data['use_by_date']:
            raise ValidationError('Pickup date cannot be later than use-by date.',
                                  field_name='pickup_date')
