from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL

app = Flask(__name__)
mysql = MySQL(app)

app.secret_key = 'tu_clave_secreta_aqui'  # Reemplaza 'tu_clave_secreta_aqui' por una cadena secreta única

# DATOS PARA CONECTARME A MI BASE DE DATOS
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'usr_01'
app.config['MYSQL_PASSWORD'] = '666'
app.config['MYSQL_DB'] = 'proyectofinalbd'

print("Conexión exitosa")

# Ruta para la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verificar las credenciales del usuario
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM login_empleado WHERE usuario = %s AND contrasena = %s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            # Iniciar sesión
            session['logged_in'] = True
            session['username'] = username
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Credenciales incorrectas. Inténtalo de nuevo.', 'error')

    return render_template('login.html')

# Ruta para ver la cuenta del usuario
@app.route('/ver_cuenta')
def ver_cuenta():
    if 'logged_in' in session:
        # Obtener el nombre de usuario de la sesión
        username = session['username']
        
        # Realizar una consulta para obtener la información del empleado
        cur = mysql.connection.cursor()
        cur.execute("SELECT e.nombre, e.apellido, e.telefono, e.fecha_ingreso, e.correo FROM empleados e JOIN login_empleado le ON e.id_empleado = le.id_empleado WHERE le.usuario = %s", (username,))
        empleado = cur.fetchone()
        cur.close()

        if empleado:
            # Pasar la información del empleado a la plantilla para mostrarla
            return render_template('ver_cuenta.html', empleado=empleado)
        else:
            flash('No se encontró información de la cuenta del usuario.', 'warning')
            return redirect(url_for('inicio'))
    else:
        flash('Debes iniciar sesión para ver tu cuenta.', 'warning')
        return redirect(url_for('login'))


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    # Cerrar la sesión
    session.clear()
    flash('¡Has cerrado sesión correctamente!', 'info')
    return redirect(url_for('login'))  # Redirige al inicio de sesión después de cerrar sesión



@app.route('/')
def inicio():
    if 'logged_in' in session:
        return render_template('inicio.html')
    else:
        return redirect(url_for('login'))


@app.route('/productos')
def productos():
    if 'logged_in' in session:
        # Consulta para obtener los productos desde la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM productos")
        productos = cur.fetchall()
        cur.close()

        # Consulta para obtener las imágenes de los productos
        imagenes = {}
        for producto in productos:
            id_producto = producto[0]
            query_imagenes = f"SELECT url_imagen FROM imagenes WHERE id_producto = {id_producto}"
            cur = mysql.connection.cursor()
            cur.execute(query_imagenes)
            imagenes[id_producto] = cur.fetchall()
            cur.close()

        # Consulta para obtener los descuentos de los productos
        descuentos = {}
        for producto in productos:
            id_producto = producto[0]
            query_descuentos = f"SELECT porcentaje FROM descuentos WHERE id_producto = {id_producto}"
            cur = mysql.connection.cursor()
            cur.execute(query_descuentos)
            descuentos[id_producto] = cur.fetchone()
            cur.close()

        return render_template('productos.html', productos=productos, imagenes=imagenes, descuentos=descuentos)
    else:
        flash('Debes iniciar sesión para ver los productos.', 'warning')
        return redirect(url_for('login'))


@app.route('/administrar_usuarios')
def administrar_usuarios():
    # Obtener los empleados desde la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM empleados")
    empleados = cur.fetchall()
    cur.close()

    # Pasar los empleados a la plantilla
    return render_template('administrar_usuarios.html', empleados=empleados)

@app.route('/agregar_usuario', methods=['GET', 'POST'])
def agregar_usuario():
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        fecha_ingreso = request.form['fecha_ingreso']

        # Insertar nuevo empleado en la tabla empleados
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO empleados (nombre, apellido, telefono, fecha_ingreso, correo) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, apellido, telefono, fecha_ingreso, email))
        mysql.connection.commit()

        # Obtener el ID del último empleado insertado
        id_empleado = cur.lastrowid

        # Insertar nuevo usuario en la tabla login_empleado
        cur.execute("INSERT INTO login_empleado (id_empleado, usuario, contrasena) VALUES (%s, %s, %s)",
                    (id_empleado, username, password))
        mysql.connection.commit()

        cur.close()

        flash('Usuario agregado correctamente', 'success')
        return redirect(url_for('agregar_usuario'))

    return render_template('agregar_usuario.html')

@app.route('/eliminar_empleado/<int:id>', methods=['POST'])
def eliminar_empleado(id):
    if request.method == 'POST':
        # Conexión a la base de datos
        cur = mysql.connection.cursor()
        
        try:
            # Eliminar los registros correspondientes en la tabla login_empleado
            cur.execute("DELETE FROM login_empleado WHERE id_empleado = %s", (id,))
            
            # Eliminar el registro de la tabla empleados
            cur.execute("DELETE FROM empleados WHERE id_empleado = %s", (id,))
            
            # Confirmar la transacción
            mysql.connection.commit()
            
            flash('Empleado eliminado correctamente', 'success')
        except Exception as e:
            flash('Error al eliminar el empleado: {}'.format(str(e)), 'error')
        
        # Cerrar el cursor
        cur.close()
        
        # Redirigir a la página de administración de usuarios
        return redirect(url_for('administrar_usuarios'))

if __name__ == '__main__':
    app.run(debug=True)


