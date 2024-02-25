# TO-DO: Limpiar comentarios.
import os, yaml
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import checkboxlist_dialog, button_dialog, message_dialog
from pykickstart.parser import KickstartParser
from pykickstart.version import makeVersion

# Ruta del archivo de kickstart generado
FILE_PATH_KS_CUSTOM= 'tmp/ks.cfg'

def packages_dict():
    # Se crea un diccionario vacío en el que se almacenarán los datos de los paquetes
    packages = {}
    for filename in os.listdir("packages"):
        if filename.endswith(".yml"):
            with open(f"packages/{filename}", "r") as file:
                package = yaml.safe_load(file)
                # Se crea un diccionario con el nombre del paquete como llave y la información como valor
                packages[package['package_name']] = package
    return packages

def packages_selection_checkboxlist_dialog():
    # Se obtiene el diccionario con la información de los paquetes
    packages = packages_dict()

    # Se crea una lista con los paquetes que se mostrarán en el checkboxlist
    package_names = []
    for key, package in packages.items():
        package_name = (key, package['name'])
        package_names.append(package_name)

    packages_selected = checkboxlist_dialog(
        title = "Fedora Kickstart Generator - Packages Selection",
        text = "Choose the packages you want to install:",
        values = package_names,
    ).run()

    # Se devuelve la lista de paquetes seleccionados
    if packages_selected is not None:
        return packages_selected
        
    return []

def package_get_info(package_name):
    packages = packages_dict()
    return packages[package_name]

def kickstart_file_generate(flavour):
    # Selecciona el archivo base dependiendo del sabor
    if flavour == 'kde':
        file_path_ks_base = 'flavours/kde-base.ks'
    elif flavour == 'gnome':
        file_path_ks_base = 'flavours/gnome-base.ks'

    # Copia el contenido del archivo base a un archivo nuevo
    with open(f"{file_path_ks_base}", 'r') as file:
        lines = file.readlines()
    
    # Crea el directorio 'tmp' si no existe
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    # Escribe el archivo nuevo con el contenido del archivo base
    with open(f"{FILE_PATH_KS_CUSTOM}", 'w') as file:
        file.writelines(lines)
        file.close()

def fedora_flavour_selection_button_dialog():
    return button_dialog(
        title = "Fedora Kickstart Generator - Flavour Selection",
        text = "Choose the flavour of Fedora you want to generate a kickstart file for:",
        buttons = [
            ("KDE", "kde"),
            ("GNOME", "gnome"),
        ],
    ).run()

def kickstart_file_add_package(package):
    # Abre el archivo de kickstart personalizado
    with open(f"{FILE_PATH_KS_CUSTOM}", 'r') as file:
        lines = file.readlines()

    # Si no se trata de un paquete RPM, añade el paquete a la lista de paquetes a instalar
    if not package['rpm']:
        # Encuentra la sección de %packages
        if "%packages\n" not in lines:
            lines.append("%packages\n")
        start = lines.index("%packages\n")
        # Encuentra en donde termina la sección de %packages teniendo en cuenta que puede haber otras secciones que también terminan con %end
        end = lines.index("%end\n", start)
        # Agrega el paquete al final de la sección de %packages sin reescribir la última línea
        lines.insert(end, f"{package['package_name'].ljust(40)}# {package['description']}\n")
    
    # Si existe un repositorio, añade la línea del repositorio justo después de la última línea que empieza con "repo --name="
    if package['third_party_repository']:
        # Encuentra la última línea que empieza con "repo --name="
        repo_line = [i for i, line in enumerate(lines) if line.startswith("repo --name=")][-1]
        # Añade la línea del repositorio justo después de la última línea que empieza con "repo --name="
        lines.insert(repo_line + 1, f"{package['third_party_repository']}\n")
    
    # Si se ha pasado el post-install por parámetro, añade las líneas de post-install justo después de la última línea de la sección de %post
    if package['post']:
        # Encuentra la sección de %post
        start = lines.index("%post --logfile=/root/post-log\n")
        # Encuentra en donde termina la sección de %post teniendo en cuenta que puede haber otras secciones que también terminan con %end
        end = lines.index("%end\n", start)
        # Añade una línea con el nombre del paquete justo antes de la última línea de la sección de %post
        lines.insert(end, f"{package['post']}\n")
        end += 1
    
    # Añade la información del paquete al archivo de kickstart personalizado
    with open (f"{FILE_PATH_KS_CUSTOM}", 'w') as file:
        file.writelines(lines)
        file.close()

def kickstart_file_validate_syntax():
    handler = makeVersion()  # Esto crea un objeto KickstartHandler de la versión más reciente
    ksparser = KickstartParser(handler)
    try:
        ksparser.readKickstart(FILE_PATH_KS_CUSTOM)
        message_dialog(
            title = "Fedora Kickstart Generator - Kickstart File Validation",
            text = f"Kickstart file {FILE_PATH_KS_CUSTOM} has been generated and validated successfully"
        ).run()
    except Exception as e:
        message_dialog(
            title = "Fedora Kickstart Generator - Kickstart File Validation",
            text = f"Kickstart file {FILE_PATH_KS_CUSTOM} has been generated with errors: {e}"
        ).run()

def main():
    # Muestra un diálogo con botones para seleccionar el sabor de Fedora y genera el archivo de kickstart
    kickstart_file_generate(fedora_flavour_selection_button_dialog())

    # Muestra un diálogo con checkboxlist para seleccionar los paquetes a instalar y los instala
    for package in packages_selection_checkboxlist_dialog():
        kickstart_file_add_package(package_get_info(package))
    
    # Validate custom kickstart file with pykickstart
    kickstart_file_validate_syntax()

if __name__ == "__main__":
    main()