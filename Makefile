#!/usr/bin/make

DEVELOPMENT_HOST := dev-odoo-18.local
ANSIBLE_PLAYBOOK := deploy.yml
ANSIBLE_USER := root

.DEFAULT_GOAL := deploy

deploy:
	ansible-playbook -i ${DEVELOPMENT_HOST}, ${ANSIBLE_PLAYBOOK} -u ${ANSIBLE_USER}
