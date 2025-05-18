# debug_form.py
# Script para insertar temporalmente en app.py para diagnosticar problemas de formulario

def debug_form_data(form, request_data):
    """
    Imprime información detallada sobre el formulario y los datos recibidos
    para ayudar a diagnosticar problemas.
    """
    print("\n===== DEBUGGING FORM DATA =====")
    print("Método de solicitud:", request.method)
    
    # Imprimir datos crudos de la solicitud
    print("\nDatos crudos de la solicitud:")
    for key, value in request_data.items():
        print(f"  {key}: {value}")
    
    # Imprimir datos del formulario
    print("\nDatos del formulario:")
    for field_name, field in form._fields.items():
        print(f"  {field_name}:")
        print(f"    Valor actual: {field.data}")
        print(f"    Valor por defecto: {field.default}")
        print(f"    Tipo: {type(field.data)}")
        print(f"    ¿Tiene errores?: {bool(field.errors)}")
        if field.errors:
            print(f"    Errores: {field.errors}")
    
    # Verificar validez del formulario
    print("\nValidación del formulario:")
    is_valid = form.validate()
    print(f"  ¿El formulario es válido?: {is_valid}")
    if not is_valid:
        print(f"  Errores: {form.errors}")
    
    print("================================\n")
    return is_valid

# Ejemplo de uso en la ruta predict:
# if request.method == 'POST':
#     debug_form_data(form, request.form)
