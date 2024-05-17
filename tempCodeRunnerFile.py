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
