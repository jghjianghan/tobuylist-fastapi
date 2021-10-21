from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from barang import Barang
import sqlite3
import os


base_url = "/barang"

# Custom errors
class NotFoundException(Exception):
    def __init__(self, nama: str):
        self.nama = nama


app = FastAPI()


class Database:
    def _connect(self):
        if os.path.exists("./daftarbelanja.sqlite"):
            return sqlite3.connect("./daftarbelanja.sqlite")
        else:
            _db = sqlite3.connect("./daftarbelanja.sqlite")
            _db.execute(
                "CREATE TABLE daftarbelanja (nama TEXT PRIMARY KEY, cek INTEGER);"
            )
            data = [
                Barang(nama="Tomat", cek=True),
                Barang(nama="Jeruk", cek=True),
                Barang(nama="Roti", cek=False),
                Barang(nama="Sabun Cuci", cek=False),
                Barang(nama="Sabun Mandi", cek=False),
            ]
            for x in data:
                _db.execute(
                    f"INSERT INTO daftarbelanja(nama, cek) VALUES ('{x.nama}', {1 if x.cek else 0});"
                )
            return _db

    def _disconnect(self, db):
        db.commit()
        db.close()

    def insert(self, barang):
        self._db.append(barang)

    def get_all(self):
        db = self._connect()
        results = db.execute("SELECT nama, cek FROM daftarbelanja").fetchall()
        self._disconnect(db)

        # return list(
        #     map(lambda row: Barang(row[0], True if row[1] == 1 else False), results)
        # )
        return list(
            map(
                lambda row: Barang(nama=row[0], cek=True if row[1] == 1 else False),
                results,
            )
        )

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
