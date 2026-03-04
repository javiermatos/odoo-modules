
# Odoo modules

Repositorio de modulos de Odoo para desarrollo.

## Despliegue

El despliegue se realiza mediante un playbook de Ansible (`deploy.yml`) que se encarga de:

1. **Copiar los modulos** al servidor remoto. Sincroniza los directorios (excluyendo archivos sueltos y elementos ocultos) hacia `/home/odoo/odoo/data/addons/available/development/`.
2. **Habilitar los modulos** creando enlaces simbolicos desde cada directorio de modulo hacia `/home/odoo/odoo/data/addons/enabled/`.
3. **Reiniciar Odoo** para que los cambios surtan efecto.

### Uso

El `Makefile` proporciona un atajo para ejecutar el playbook:

```bash
make deploy
```

Esto equivale a:

```bash
ansible-playbook -i dev-odoo-18.local, deploy.yml -u root
```

### Variables del Makefile

| Variable             | Valor por defecto      | Descripcion                        |
|----------------------|------------------------|------------------------------------|
| `DEVELOPMENT_HOST`   | `dev-odoo-18.local`    | Host de destino                    |
| `ANSIBLE_PLAYBOOK`   | `deploy.yml`           | Playbook a ejecutar                |
| `ANSIBLE_USER`       | `root`                 | Usuario SSH para la conexion       |

Se pueden sobreescribir al invocar `make`:

```bash
make deploy DEVELOPMENT_HOST=otro-host.local ANSIBLE_USER=admin
```
