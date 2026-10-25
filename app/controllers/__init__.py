def register_blueprints(app):
    from .category_controller import bp as category_bp
    from .customer_controller import bp as customer_bp
    from .order_controller import bp as order_bp
    from .product_controller import bp as product_bp

    for blueprint in (category_bp, product_bp, customer_bp, order_bp):
        app.register_blueprint(blueprint)
