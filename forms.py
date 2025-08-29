from wtforms import Form, StringField, FloatField
from wtforms.validators import InputRequired, Length, NumberRange

class StudentForm(Form):
    name = StringField('Name', [InputRequired(), Length(min=1, max=120)])
    roll_number = StringField('Roll Number', [InputRequired(), Length(min=1, max=50)])

class GradeForm(Form):
    subject = StringField('Subject', [InputRequired(), Length(min=1, max=80)])
    score = FloatField('Score', [InputRequired(), NumberRange(min=0, max=100)])
