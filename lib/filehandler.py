class BufferFileHandler:
  BUFFER_SIZE = 32756
  
  def __init__(self, path: str, flag:str):
    self.path = path
    self.file = open(self.path, flag)
  
  def get_content(self, i):
    self.file.seek(i * self.BUFFER_SIZE)
    return self.file.read(self.BUFFER_SIZE)
  
  def write(self, content):
    self.file.write(content)
  
  def __del__(self):
    self.file.close()
    
