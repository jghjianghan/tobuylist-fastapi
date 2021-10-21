from pydantic.main import BaseModel


class Barang(BaseModel):
    nama: str
    cek = False
