from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,SelectField
from wtforms.validators import DataRequired,Length,EqualTo,IPAddress,Regexp
from wtforms import ValidationError,BooleanField
from .db import get_db
import ipaddress,re
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
    net_work = SelectField('所属网络', validators=[
        DataRequired(message="请选择所属网络")
    ])
    submit = SubmitField('下一步')

class AddInterfaceForm(FlaskForm):
    interface_name = StringField(
        '接口名称',
        validators=[
            DataRequired(message="接口名称不能为空"),
            Regexp(r'^[a-zA-Z0-9_-]{1,15}$', message="只能包含字母、数字、下划线、短横线，且长度不超过15个字符")
        ]
    )

    address = SelectField(
        'Address Pool',
        choices=[
            ('24', '小型 - 支持约 255 客户端'),
            ('23', '中型 - 支持约 510 客户端'),
            ('22', '大型 - 支持约 1022 客户端'),
            ('21', '巨型 - 支持约 2046 客户端'),
        ]
    )

    server_ip = StringField('服务器IP地址')  

    use_domain = BooleanField('使用域名')

    domain = StringField('域名', validators=[
        Length(max=255, message="域名长度不能超过255个字符")
    ])

    DNS = StringField('DNS服务器', default='8.8.8.8', validators=[
        DataRequired(message="DNS服务器不能为空"),
        IPAddress(ipv4=True, message="请输入有效的IPv4地址")
    ])

    submit = SubmitField('添加')

    def validate_domain(self, field):
     if self.use_domain.data:
         if not field.data or field.data.strip() == '':
             raise ValidationError("选择使用域名时，域名不能为空")
        
         domain_pattern = re.compile(
             r'^(?=.{1,255}$)([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+[a-zA-Z]{2,63}$'
         )
         if not domain_pattern.match(field.data.strip()):
             raise ValidationError("请输入有效的域名，例如 example.com")

    def validate_server_ip(self, field):
        if not self.use_domain.data:
            if not field.data or field.data.strip() == '':
                raise ValidationError("请输入服务器IP地址，或使用域名。")
            try:
                ipaddress.IPv4Address(field.data)
            except ValueError:
                raise ValidationError("请输入有效的IPv4地址")
class PasswordResetForm(FlaskForm):
    new_password = PasswordField("新密码", validators=[
        DataRequired(), Length(min=8)
    ])
    confirm_password = PasswordField("确认新密码", validators=[
        DataRequired(), EqualTo('new_password', message="两次输入的密码必须一致.")
    ])
    submit = SubmitField("重置密码") 
class EmptyForm(FlaskForm):
    pass


    