class ServerConfig:
  __IP = "localhost"
  __PORT = 8080
  __WINDOW_SIZE = 16

  @property
  def IP(self):
    return self.__IP

  @property
  def PORT(self):
    return self.__PORT

  @property
  def WINDOW_SIZE(self):
    return self.__WINDOW_SIZE


config = ServerConfig()
