from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL

app = Flask(__name__)
mysql = MySQL(app)

app.secret_key = 'clave_secreta' 

# DATOS PARA CONECTARME A MI BASE DE DATOS
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'usr_01'
app.config['MYSQL_PASSWORD'] = '666'
app.config['MYSQL_DB'] = 'sqlproyectofinalalex'

print("Conexión exitosa")

# Ruta para la página de inicio de sesión
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

        if user:
            id_empleado = user[1]  # Usamos el índice correspondiente al id_empleado
            # Obtener el rol del usuario
            cur.execute("SELECT rol FROM empleados WHERE id_empleado = %s", (id_empleado,))
            empleado = cur.fetchone()
            cur.close()

            if empleado:
                rol = empleado[0]  # Usamos el índice correspondiente al rol
                # Iniciar sesión
                session['logged_in'] = True
                session['username'] = username
                session['rol'] = rol
                
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('inicio'))
            else:
                flash('No se pudo encontrar el rol del usuario.', 'error')
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

## RUTAS PARA GESTIONAR USUARIOS

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
        rol = request.form['rol']  # Nuevo campo para el rol del usuario

        # Insertar nuevo empleado en la tabla empleados
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO empleados (nombre, apellido, telefono, fecha_ingreso, correo, rol) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre, apellido, telefono, fecha_ingreso, email, rol))
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


@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
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

## RUTAS PARA GESTIONAR PRODUCTOS

@app.route('/gestionar_productos')
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
            cur.execute("""
                SELECT categorias.nombre_categoria 
                FROM categorias 
                INNER JOIN productos ON productos.id_categoria = categorias.id_categoria
                WHERE productos.id_producto = %s
            """, (id_producto,))
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

        return render_template('gestionar_productos.html', productos=productos, imagenes=imagenes, descuentos=descuentos, stocks=stocks, categorias=categorias, marcas=marcas)
    else:
        flash('Debes iniciar sesión para ver los productos.', 'warning')
        return redirect(url_for('login'))

@app.route('/productos/agregar', methods=['GET', 'POST'])
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

@app.route('/productos/<int:id>/eliminar', methods=['POST'])
def eliminar_producto(id):
    if request.method == 'POST':
        # Conexión a la base de datos
        cur = mysql.connection.cursor()
        try:
            # Eliminar los registros relacionados en otras tablas
            cur.execute("DELETE FROM descuentos WHERE id_producto = %s", (id,))
            cur.execute("DELETE FROM detalle_carritos WHERE id_producto = %s", (id,))
            cur.execute("DELETE FROM detalle_pedidos WHERE id_producto = %s", (id,))
            cur.execute("DELETE FROM imagenes WHERE id_producto = %s", (id,))
            cur.execute("DELETE FROM imagen_resenas WHERE id_resena IN (SELECT id_resena FROM resenas WHERE id_producto = %s)", (id,))
            cur.execute("DELETE FROM resenas WHERE id_producto = %s", (id,))
            # Luego eliminar el producto de la tabla productos
            cur.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
            # Confirmar la transacción
            mysql.connection.commit()
            flash('Producto eliminado correctamente', 'success')
        except Exception as e:
            flash(f'Error al eliminar el producto: {str(e)}', 'error')
        finally:
            cur.close()
    return redirect('/gestionar_productos')

@app.route('/productos/<int:id>/editar', methods=['GET', 'POST'])
def editar_producto(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        nombre_producto = request.form['nombre_producto']
        descripcion_producto = request.form['descripcion_producto']
        id_categoria = request.form['categoria_producto']
        id_marca = request.form['marca_producto']
        stock = request.form['stock']
        precio = request.form['precio']
        
        if stock:
            stock = int(stock)
        else:
            stock = None

        # Actualización de productos
        cur.execute("""
            UPDATE productos 
            SET nombre_producto = %s, descripcion_producto = %s, id_marca = %s, id_categoria = %s, precio = %s
            WHERE id_producto = %s
        """, (nombre_producto, descripcion_producto, id_marca, id_categoria, precio, id))

        # Obtener id_stock del producto
        cur.execute("SELECT id_stock FROM productos WHERE id_producto = %s", (id,))
        stockinfo = cur.fetchone()
        
        if stockinfo and stock is not None:
            id_stock = stockinfo[0]
            # Actualizar la cantidad de stock
            cur.execute("UPDATE stocks SET cantidad_stock = %s WHERE id_stock = %s", (stock, id_stock))
        
        mysql.connection.commit()
        cur.close()

        flash('Producto editado correctamente', 'success')
        return redirect('/gestionar_productos')
    else:
        cur.execute("SELECT * FROM productos WHERE id_producto = %s", (id,))
        producto = cur.fetchone()

        cur.execute("SELECT * FROM categorias")
        categorias = cur.fetchall()

        cur.execute("SELECT * FROM marcas")
        marcas = cur.fetchall()

        cur.close()

        if producto:
            id_marca = producto[4]
            id_categoria = producto[5]
            id_stock = producto[3]

            cur = mysql.connection.cursor()
            cur.execute("SELECT nombre_marca FROM marcas WHERE id_marca = %s", (id_marca,))
            nombre_producto_marca = cur.fetchone()[0]

            cur.execute("SELECT nombre_categoria FROM categorias WHERE id_categoria = %s", (id_categoria,))
            nombre_producto_categoria = cur.fetchone()[0]
                                                       
            cur.execute("SELECT cantidad_stock FROM stocks WHERE id_stock = %s", (id_stock,))
            stock = cur.fetchone()[0]

            cur.close()
            return render_template('editar_producto.html', producto=producto, categorias=categorias, marcas=marcas, nombre_producto_marca=nombre_producto_marca, nombre_producto_categoria=nombre_producto_categoria, stock=stock)
        else:
            flash('El producto no existe', 'error')
            return redirect('/gestionar_productos')

@app.route('/pedidos/<int:pedido_id>/actualizar_estado', methods=['POST'])
def actualizar_estado_pedido(pedido_id):
    nuevo_estado = request.form['nuevo_estado']
    
    cursor = mysql.connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE pedidos
            SET id_estado_pedido = %s
            WHERE id_pedido = %s
        """, (nuevo_estado, pedido_id))
        
        mysql.connection.commit()
        flash('El estado del pedido ha sido actualizado con éxito.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al actualizar el estado del pedido: {e}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('administrar_pedidos'))



@app.route('/productos/<int:id_producto>/imagenes', methods=['GET', 'POST'])
def administrar_imagenes_producto(id_producto):
    if request.method == 'POST':
        # Obtener la URL de la imagen desde el formulario
        url_imagen = request.form['url_imagen']
        if url_imagen:
            # Conexión a la base de datos
            cur = mysql.connection.cursor()
            try:
                # Insertar la URL de la imagen en la tabla imagenes
                cur.execute("INSERT INTO imagenes (id_producto, url_imagen) VALUES (%s, %s)", (id_producto, url_imagen))
                # Confirmar la transacción
                mysql.connection.commit()
                flash('Imagen actualizada correctamente', 'success')
            except Exception as e:
                flash(f'Error al actualizar la imagen: {str(e)}', 'error')
            finally:
                cur.close()
            return redirect(url_for('administrar_imagenes_producto', id_producto=id_producto))

    # Obtener las imágenes actuales del producto
    cur = mysql.connection.cursor()
    cur.execute("SELECT url_imagen FROM imagenes WHERE id_producto = %s", (id_producto,))
    imagenes = cur.fetchall()
    cur.close()

    # Renderizar el formulario para editar imágenes
    return render_template('administrar_imagenes_producto.html', id_producto=id_producto, imagenes=imagenes)

@app.route('/eliminar_imagen', methods=['POST'])
def eliminar_imagen():
    if request.method == 'POST':
        # Obtener la URL de la imagen y el ID del producto desde el formulario
        imagen_url = request.form['imagen_url']
        id_producto = request.form['id_producto']
        if imagen_url and id_producto:
            # Conexión a la base de datos
            cur = mysql.connection.cursor()
            try:
                # Eliminar la imagen de la tabla imagenes
                cur.execute("DELETE FROM imagenes WHERE url_imagen = %s AND id_producto = %s", (imagen_url, id_producto))
                # Confirmar la transacción
                mysql.connection.commit()
                flash('Imagen eliminada correctamente', 'success')
            except Exception as e:
                flash(f'Error al eliminar la imagen: {str(e)}', 'error')
            finally:
                cur.close()
    return redirect(url_for('administrar_imagenes_producto', id_producto=id_producto))



## RUTAS PARA GESTIONAR SITIO

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
        return redirect('/mostrar_sitio')

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

## RUTAS PARA GESTIONAR DESCUENTOS

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
        codigo_producto = request.form['codigo_producto']
        estado_descuento = request.form['estado_descuento']
        tipo_descuento = request.form['tipo_descuento']
        codigo = request.form['codigo']
        cantidad = request.form['cantidad']
        if cantidad:
            cantidad = int(cantidad)
        else:
            cantidad = None
        porcentaje = request.form['porcentaje']
        if porcentaje:
            porcentaje = int(porcentaje)
        else:
            porcentaje = None
        descripcion = request.form['descripcion']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        
        # Actualizar el descuento en la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                UPDATE descuentos 
                SET id_producto = %s, id_estado_descuento = %s, codigo = %s, id_tipo_descuento = %s, cantidad = %s, fecha_inicio = %s, fecha_fin = %s, porcentaje = %s, descripcion = %s
                WHERE id_descuento = %s
            """, (codigo_producto, estado_descuento, codigo, tipo_descuento, cantidad, fecha_inicio, fecha_fin, porcentaje, descripcion, id))
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

@app.route('/descuentos/agregar', methods=['GET', 'POST'])
def agregar_descuento():
    if request.method == 'POST':
        codigo_producto = request.form['codigo_producto']
        estado_descuento = request.form['estado_descuento']
        tipo_descuento = request.form['tipo_descuento']
        codigo = request.form['codigo']
        cantidad = request.form['cantidad']
        cantidad = int(cantidad) if cantidad else None
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        porcentaje = request.form['porcentaje']
        porcentaje = int(porcentaje) if porcentaje else None
        descripcion = request.form['descripcion']

        # Obtener las categorías desde la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO descuentos (id_producto, id_estado_descuento, codigo, id_tipo_descuento, cantidad, fecha_inicio, fecha_fin, porcentaje, descripcion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (codigo_producto, estado_descuento, codigo, tipo_descuento, cantidad, fecha_inicio, fecha_fin, porcentaje, descripcion))
            mysql.connection.commit()
            flash('Descuento agregado correctamente', 'success')
            return redirect('/gestionar_descuentos')
        except Exception as e:
            flash('Error al agregar el descuento', 'error')
            print(e)  # Imprimir el error para depuración
            return redirect('/gestionar_descuentos')
        finally:
            cur.close()

    return render_template('agregar_descuento.html')

## RUTAS PARA GESTIONAR CATEGORIAS

@app.route('/gestionar_categorias')
def gestionar_categorias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categorias")
    categorias = cur.fetchall()
    cur.close()
    return render_template('gestionar_categorias.html', categorias=categorias)

@app.route('/categorias/<int:id>/editar', methods=['GET', 'POST'])
def editar_categoria(id):
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        
        # Actualizar el descuento en la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute("UPDATE categorias SET nombre_categoria = %s WHERE id_categoria = %s", (nombre_categoria, id))
            mysql.connection.commit()
            flash('categoria editada correctamente', 'success')
            return redirect('/gestionar_categorias')
        except Exception as e:
            flash('Error al editar la categoria', 'error')
            print(e)
            return redirect('/gestionar_categorias')
        finally:
            cur.close()
    else:
        # Obtener los datos del descuento existente de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categorias WHERE id_categoria = %s", (id,))
        categoria = cur.fetchone()
        cur.close()

        if categoria:
            return render_template('editar_categoria.html', categoria=categoria)
        else:
            flash('La categoria no existe', 'error')
            return redirect('/gestionar_categorias')

@app.route('/categorias/<int:id>/eliminar', methods=['POST'])
def eliminar_categoria(id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        try:
            # Eliminar el registro de la tabla descuentos
            cur.execute("DELETE FROM categorias WHERE id_categoria = %s", (id,))
            
            # Confirmar la transacción
            mysql.connection.commit()
            
            flash('Categoria eliminada correctamente', 'success')
        except Exception as e:
            flash('Error al eliminar la categoria', 'error')
        
        # Cerrar el cursor
        cur.close()
    return redirect('/gestionar_categorias')

@app.route('/categorias/agregar', methods=['GET', 'POST'])
def agregar_categoria():
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']

        # Obtener las categorías desde la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO categorias (nombre_categoria) VALUES (%s)", (nombre_categoria,))
            mysql.connection.commit()
            flash('categoria agregada correctamente', 'success')
            return redirect('/gestionar_categorias')
        except Exception as e:
            flash('Error al agregar la categoria', 'error')
            print(e)  # Imprimir el error para depuración
            return redirect('/gestionar_categorias')
        finally:
            cur.close()

    return render_template('agregar_categoria.html')

## RUTAS PARA GESTIONAR PEDIDOS


@app.route('/administrar_pedidos')
def administrar_pedidos():
    cur = mysql.connection.cursor()
    query = """
    SELECT pedidos.id_pedido, 
           CONCAT(clientes.nombre, ' ', clientes.apellido) AS cliente, 
           estado_pedidos.nombre AS estado, 
           pedidos.id_estado_pedido 
    FROM pedidos 
    JOIN clientes ON pedidos.id_cliente = clientes.id_cliente 
    JOIN estado_pedidos ON pedidos.id_estado_pedido = estado_pedidos.id_estado_pedido
    """
    cur.execute(query)
    pedidos = cur.fetchall()

    cur.execute("SELECT * FROM estado_pedidos")
    estados_pedidos = cur.fetchall()
    
    # Obtener detalles de los pedidos
    cur.execute("SELECT * FROM detalle_pedidos")
    detalle_pedidos = cur.fetchall()
    
    cur.close()
    
    return render_template('administrar_pedidos.html', pedidos=pedidos, estados_pedidos=estados_pedidos, detalle_pedidos=detalle_pedidos)

@app.route('/detalle_pedidos/<int:id_pedido>')
def detalle_pedido(id_pedido):
    cur = mysql.connection.cursor()

    # Obtener los detalles del pedido
    cur.execute("""
        SELECT pedidos.id_pedido, pedidos.id_cliente, clientes.nombre, clientes.apellido, estado_pedidos.nombre
        FROM pedidos 
        JOIN clientes ON pedidos.id_cliente = clientes.id_cliente 
        JOIN estado_pedidos ON pedidos.id_estado_pedido = estado_pedidos.id_estado_pedido 
        WHERE pedidos.id_pedido = %s
    """, (id_pedido,))
    pedido = cur.fetchone()

    # Obtener los productos asociados al pedido
    cur.execute("""
        SELECT productos.nombre_producto, productos.descripcion_producto, productos.precio, marcas.nombre_marca, detalle_pedidos.cantidad
        FROM detalle_pedidos 
        JOIN productos ON detalle_pedidos.id_producto = productos.id_producto  
        JOIN marcas ON productos.id_marca = marcas.id_marca 
        WHERE detalle_pedidos.id_pedido = %s
    """, (id_pedido,))
    productos_pedido = cur.fetchall()

    cur.close()

    return render_template('detalle_pedidos.html', pedido=pedido, productos_pedido=productos_pedido)

@app.route('/reportes_estadisticas')
def reportes_estadisticas():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.nombre_producto, COUNT(dp.id_producto) AS cantidad 
        FROM detalle_pedidos AS dp 
        JOIN productos AS p ON dp.id_producto = p.id_producto 
        GROUP BY p.id_producto 
        ORDER BY cantidad DESC
        LIMIT 5;
    """)
    ventas = cur.fetchall()
    cur.execute("""
        SELECT ep.nombre, COUNT(p.id_estado_pedido) AS cantidad
        FROM estado_pedidos AS ep
        JOIN pedidos AS p ON ep.id_estado_pedido = p.id_estado_pedido
        GROUP BY ep.nombre
        ORDER BY cantidad DESC;
    """)
    estados = cur.fetchall()
    cur.close()
    
    data_estados = [{"name": estado[0], "y": estado[1]} for estado in estados]
    data_ventas = [{"name": venta[0], "y": venta[1]} for venta in ventas]
    
    return render_template('reportes_estadisticas.html', estados=estados, ventas=ventas, data_ventas=data_ventas, data_estados=data_estados)

if __name__ == '__main__':
    app.run(debug=True)