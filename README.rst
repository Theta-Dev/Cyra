####
Cyra
####

Cyra is a simple config framework for Python.

Cyra's ConfigBuilder makes it easy to specify your configuration.
The config can be read from and written to a toml file.

If the config file does not exist, Cyra will generate a new one populated with initial
values and annotated with helpful comments.

Checklist (development)
#######################
- [X] Config builder
- [X] Value fields (string, int, bool, list, dict)
- [ ] Value verification
- [X] Infinite nesting
- [X] Comments
- [X] Load/generate config from file
- [X] Write config back to file
- [ ] Sphinx Autodoc
