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

        # Consulta para obtener las imágenes de los productos
        imagenes = {}
        for producto in productos:
            id_producto = producto[0]
            query_imagenes = f"SELECT url_imagen FROM imagenes WHERE id_producto = {id_producto}"
            cur.execute(query_imagenes)
            imagenes[id_producto] = cur.fetchall()

        # Consulta para obtener los descuentos de los productos
        descuentos = {}
        for producto in productos:
            id_producto = producto[0]
            query_descuentos = f"SELECT porcentaje FROM descuentos WHERE id_producto = {id_producto}"
            cur.execute(query_descuentos)
            descuentos[id_producto] = cur.fetchone()

        # Consulta para obtener los stocks de los productos
        stocks = {}
        for producto in productos:
            id_producto = producto[0]
            cur.execute("SELECT cantidad_stock FROM stocks WHERE id_stock = %s", (producto[3],))
            stock = cur.fetchone()
            stocks[id_producto] = stock[0]

        # Consulta para obtener las categorías de los productos
        categorias = {}
        for producto in productos:
            id_producto = producto[0]
            cur.execute("SELECT nombre_categoria FROM categorias WHERE id_categoria = %s", (producto[5],))
            categorias[id_producto] = [row[0] for row in cur.fetchall()]

        # Consulta para obtener las marcas de los productos
        marcas = {}
        for producto in productos:
            id_marca = producto[4]  # Obtener el ID de la marca del producto
            cur.execute("SELECT nombre_marca FROM marcas WHERE id_marca = %s", (id_marca,))
            marca = cur.fetchone()
            marcas[producto[0]] = marca[0] if marca else "Marca desconocida"  # Asociar la marca al ID del producto
            
        cur.close()

        # Preenumerar la lista de imágenes
        for id_producto, lista_imagenes in imagenes.items():
            imagenes[id_producto] = list(enumerate(lista_imagenes))

        return render_template('productos.html', productos=productos, imagenes=imagenes, descuentos=descuentos, stocks=stocks, categorias=categorias,marcas=marcas)
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
    
@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre_producto = request.form['nombre_producto']
        descripcion_producto = request.form['descripcion_producto']
        id_stock = request.form['id_stock']
        id_marca = request.form['id_marca']
        imagen_producto = request.form['imagen_producto']  # Obtener la URL de la imagen

        # Obtener las categorías desde la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorias")
        categorias = cur.fetchall()
        cur.close()

        return render_template('agregar_producto.html', categorias=categorias)

    return render_template('agregar_producto.html')


@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    if request.method == 'POST':
        # Manejar el envío del formulario para editar el producto aquí
        # Recuperar los datos del formulario, actualizar la base de datos, etc.
        flash('Producto editado correctamente', 'success')
        return redirect(url_for('productos'))
    else:
        # Obtener los datos del producto existente de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM productos WHERE id_producto = %s", (producto_id,))
        producto = cur.fetchone()
        cur.close()

        # Verificar si el producto existe
        if producto:
            # Pasar los datos del producto a la plantilla para rellenar los campos del formulario
            return render_template('editar_producto.html', producto=producto)
        else:
            flash('El producto no existe', 'error')
            return redirect(url_for('productos'))

        
@app.route('/configurar_sitio', methods=['GET', 'POST'])
def configurar_sitio():
    mensaje = None
    # Consultar los datos de la tienda desde la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tienda")
    tienda = cur.fetchone()
    cur.close()
    
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre_tienda = request.form['nombre_tienda']
        calle = request.form['calle']
        colonia = request.form['colonia']
        codigo_postal = request.form['codigo_postal']
        ciudad = request.form['ciudad']
        estado = request.form['estado']
        pais = request.form['pais']
        telefono = request.form['telefono']
        email = request.form['email']
        
        # Actualizar los datos de la tienda en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE tienda 
            SET nombre_tienda = %s, 
                calle = %s, 
                colonia = %s, 
                codigo_postal = %s, 
                ciudad = %s, 
                estado = %s, 
                pais = %s, 
                telefono = %s, 
                email = %s
            WHERE id_tienda = %s
        """, (nombre_tienda, calle, colonia, codigo_postal, ciudad, estado, pais, telefono, email, tienda[0]))
        mysql.connection.commit()
        cur.close()
        
        # Configurar mensaje de cambio exitoso
        flash('Cambio exitoso', 'success')
        return redirect(url_for('configurar_sitio'))

    # Si es un método GET o POST, renderiza el formulario con los datos de la tienda
    return render_template('configurar_sitio.html', tienda=tienda, mensaje=mensaje)

@app.route('/mostrar_sitio')
def mostrar_sitio():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tienda WHERE id_tienda = 1")
    tienda = cur.fetchone()
    cur.close()
    if tienda:
        return render_template('mostrar_sitio.html', tienda=tienda)
    else:
        return "La tienda no se encontró en la base de datos"

@app.route('/gestionar_categorias')
def gestionar_categorias():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorias")
        categorias = cur.fetchall()
        cur.close()
        print("Categorías recuperadas:", categorias)  # Mensaje de depuración
        return render_template('gestionar_categorias.html', categorias=categorias)
    except Exception as e:
        print("Error al recuperar categorías:", e)  # Mensaje de error
        return "Error al recuperar categorías", 500
    
@app.route('/agregar_categoria', methods=['GET', 'POST'])
def crear_categoria():
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO categorias (nombre_categoria) VALUES (%s)", (nombre_categoria,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('gestionar_categorias'))
    return render_template('agregar_categoria.html')

@app.route('/eliminar_categoria/<int:id_categoria>', methods=['POST'])
def eliminar_categoria(id_categoria):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM categorias WHERE id_categoria = %s", (id_categoria,))
        mysql.connection.commit()

        return redirect(url_for('gestionar_categorias'))
    
@app.route('/editar_categoria/<int:id_categoria>', methods=['GET', 'POST'])
def editar_categoria(id_categoria):
    if request.method == 'POST':
        cur = None
        try:
            nombre_categoria = request.form['nombre_categoria']
            cur = mysql.connection.cursor()
            cur.execute("UPDATE categorias SET nombre_categoria = %s WHERE id_categoria = %s", (nombre_categoria, id_categoria))
            mysql.connection.commit()
            flash('Categoría editada correctamente', 'success')
            return redirect('/gestionar_categorias')
        except Exception as e:
            flash('Error al editar la categoría', 'error')
            print(e)  # Imprimir el error para depuración
            return redirect('/gestionar_categorias')
        finally:
            if cur:  # Verificar si cur está definido antes de cerrarlo
                cur.close()
    else:
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM categorias WHERE id_categoria = %s", (id_categoria,))
            categoria = cur.fetchone()
            cur.close()

            # Verificar si la categoría existe
            if categoria:
                # Pasar los datos de la categoría a la plantilla para rellenar los campos del formulario
                return render_template('editar_categoria.html', categoria=categoria)
            else:
                flash('La categoría no existe', 'error')
                return redirect('/gestionar_categorias')
        finally:
            if cur:  # Verificar si cur está definido antes de cerrarlo
                cur.close()









@app.route('/gestionar_descuentos')
def gestionar_descuentos():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM descuentos")
    descuentos = cur.fetchall()
    cur.close()
    return render_template('gestionar_descuentos.html', descuentos=descuentos)

@app.route('/descuentos/<int:id>/editar', methods=['GET', 'POST'])
def editar_descuento(id):
    if request.method == 'POST':
        # Capturar los datos enviados por el formulario
        codigo = request.form['codigo']
        cantidad = request.form['cantidad']
        if cantidad:
            cantidad = int(cantidad)
        else:
            cantidad = None
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        porcentaje = request.form['porcentaje']
        if porcentaje:
            porcentaje = int(porcentaje)
        else:
            porcentaje = None
        descripcion = request.form['descripcion']
        
        # Actualizar el descuento en la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                UPDATE descuentos 
                SET codigo = %s, cantidad = %s, fecha_inicio = %s, fecha_fin = %s, porcentaje = %s, descripcion = %s
                WHERE id_descuento = %s
            """, (codigo, cantidad, fecha_inicio, fecha_fin, porcentaje, descripcion, id))
            mysql.connection.commit()
            flash('Descuento editado correctamente', 'success')
            return redirect('/gestionar_descuentos')
        except Exception as e:
            flash('Error al editar el descuento', 'error')
            print(e)  # Imprimir el error para depuración
            return redirect('/gestionar_descuentos')
        finally:
            cur.close()
    else:
        # Obtener los datos del descuento existente de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM descuentos WHERE id_descuento = %s", (id,))
        descuento = cur.fetchone()
        cur.close()

        # Verificar si el descuento existe
        if descuento:
            # Pasar los datos del descuento a la plantilla para rellenar los campos del formulario
            return render_template('editar_descuentos.html', descuento=descuento)
        else:
            flash('El descuento no existe', 'error')
            return redirect('/gestionar_descuentos')

@app.route('/descuentos/<int:id>/eliminar', methods=['POST'])
def eliminar_descuento(id):
    if request.method == 'POST':
        # Conexión a la base de datos
        cur = mysql.connection.cursor()
        try:
            # Eliminar el registro de la tabla descuentos
            cur.execute("DELETE FROM descuentos WHERE id_descuento = %s", (id,))
            
            # Confirmar la transacción
            mysql.connection.commit()
            
            flash('Descuento eliminado correctamente', 'success')
        except Exception as e:
            flash('Error al eliminar el descuento', 'error')
        
        # Cerrar el cursor
        cur.close()
    
    return redirect('/gestionar_descuentos')


if __name__ == '__main__':
    app.run(debug=True)