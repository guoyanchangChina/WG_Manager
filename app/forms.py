from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,SelectField
from wtforms.validators import DataRequired,Length,EqualTo,IPAddress
from wtforms import ValidationError
from .db import get_db

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": "Enter your username"})
    password = PasswordField('密码', validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": "Enter your password"})
    submit = SubmitField('登录', render_kw={"class": "submit-btn"})

class EditUserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('密码', validators=[
        Length(min=6),
        EqualTo('confirm', message='两次输入的密码不一致')
    ])
    confirm = PasswordField('确认密码')  
    department = SelectField('部门',choices=[('电气','电气'),('实施','实施'),('研发','研发'),('售后','售后')], validators=[DataRequired()])
    role = SelectField('角色', choices=[('user', 'User'), ('admin', 'Admin')], default='user')
    submit = SubmitField('提交')

    def __init__(self, is_edit=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_edit = is_edit
        if is_edit:
            self.password.validators = []  
            self.confirm.validators = []  
        else:
            self.password.validators = [DataRequired(), Length(min=6)] + list(self.password.validators)
            self.confirm.validators = [DataRequired(), Length(min=6), EqualTo('password', message='两次输入的密码不一致')]
            self.password.render_kw = {'required': True}
            self.confirm.render_kw = {'required': True}

    def validate_username(self, field):
        if self.is_edit:
            return
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (field.data,))
        if cursor.fetchone():
            raise ValidationError("用户名已存在")
        
class AddClientForm(FlaskForm):
    name = StringField('客户端名称', validators=[
        DataRequired(message="必须输入一个名称！"),
        Length(max=64)],        )
    
    submit = SubmitField('下一步')

class EmptyForm(FlaskForm):
    pass