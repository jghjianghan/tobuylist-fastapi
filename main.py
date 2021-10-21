from enum import Flag
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from barang import Barang

base_url = "/barang"

# Custom errors
class NotFoundException(Exception):
    def __init__(self, nama: str):
        self.nama = nama


app = FastAPI()


class Database:
    def __init__(self):
        self._db = [
            Barang(nama="Tomat", cek=True),
            Barang(nama="Jeruk", cek=True),
            Barang(nama="Roti", cek=False),
            Barang(nama="Sabun Cuci", cek=False),
            Barang(nama="Sabun Mandi", cek=False),
        ]

    def insert(self, barang):
        self._db.append(barang)

    def get_all(self):
        return self._db

    def get_by_name(self, nama):
        return next((barang for barang in self._db if barang.nama == nama))

    def delete(self, nama):
        item = next((barang for barang in self._db if barang.nama == nama))
        self._db.remove(item)
        return item

    def toggle(self, nama):
        for i in range(len(self._db)):
            if self._db[i].nama == nama:
                self._db[i].cek = not self._db[i].cek
                return self._db[i]

        raise NotFoundException(nama)


db = Database()


@app.exception_handler(NotFoundException)
def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": f"{exc.nama} tidak ditemukan"},
    )


@app.get(base_url + "/")
def get_all_barang():
    return {"status": "ok", "items": db.get_all()}


@app.get(base_url + "/{nama_barang}")
def get_barang_by_nama(nama_barang):
    try:
        return {"status": "ok", "item": db.get_by_name(nama_barang)}
    except StopIteration:
        raise NotFoundException(nama_barang)


@app.put(base_url + "/{nama_barang}", status_code=201)
def create_barang(nama_barang):
    barang_baru = Barang(nama=nama_barang)
    db.insert(barang_baru)
    return {"status": "ok", "item": barang_baru}


@app.delete(base_url + "/{nama_barang}")
def delete_barang(nama_barang):
    try:
        return {"status": "ok", "item": db.delete(nama_barang)}
    except StopIteration:
        raise NotFoundException(nama_barang)


@app.post(base_url + "/{nama_barang}")
def toggle_barang(nama_barang):
    return {"status": "ok", "item": db.toggle(nama_barang)}
