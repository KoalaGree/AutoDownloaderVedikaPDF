import configparser
import os

class Config:
    def __init__(self, config_path='app.config'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        self.Database = self.DatabaseConfig(self.config)
        self.Paths = self.PathsConfig(self.config)
        self.Url = self.UrlConfig(self.config)
        self.UserPass = self.UserPassConfig(self.config)

    class DatabaseConfig:
        def __init__(self, config):
            self.host = config['Database'].get('Host')
            self.port = config['Database'].getint('Port')
            self.database = config['Database'].get('Database')
            self.user = config['Database'].get('User')
            self.password = config['Database'].get('Password')

    class PathsConfig:
        def __init__(self, config):
            self.base_path = config['Paths'].get('base_path')
            self.wkhtmlfolder = config['Paths'].get('path_wkthmltopdf')

    class UrlConfig:
        def __init__(self, config):
            self.jkn = config['Url'].get('jknurl')
            self.mlite = config['Url'].get('mlite')

    class UserPassConfig:
        def __init__(self, config):
            self.username = config['UserPass'].get('USERNAME')
            self.password = config['UserPass'].get('PASSWORD')
