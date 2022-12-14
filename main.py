from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import RedirectResponse
from barang import Barang
import sqlite3
import os


base_url = "/barangbswkm"

# Custom errors
class NotFoundException(Exception):
    def __init__(self, nama: str):
        self.nama = nama


class ServerException(Exception):
    def __init__(self, message: str):
        self.message = message


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
                    "INSERT INTO daftarbelanja(nama, cek) VALUES (?, ?);",
                    (x.nama, 1 if x.cek else 0),
                )
            return _db

    def _disconnect(self, db):
        db.commit()
        db.close()

    def insert(self, barang: Barang):
        db = self._connect()

        try:
            db.execute(
                "INSERT INTO daftarbelanja(nama, cek) VALUES (?, ?)",
                (barang.nama, 1 if barang.cek else 0),
            )
        except sqlite3.Error as e:
            raise ServerException(e.args[0])
        finally:
            self._disconnect(db)

        return barang

    def get_all(self):
        db = self._connect()
        results = db.execute("SELECT nama, cek FROM daftarbelanja").fetchall()
        self._disconnect(db)

        return list(
            map(
                lambda row: Barang(nama=row[0], cek=(row[1] == 1)),
                results,
            )
        )

    def get_by_name(self, nama):
        db = self._connect()
        row = db.execute(
            "SELECT nama, cek FROM daftarbelanja WHERE nama=?", (nama,)
        ).fetchone()
        self._disconnect(db)
        if row is None:
            raise NotFoundException(nama)
        else:
            return Barang(nama=row[0], cek=(row[1] == 1))

    def delete(self, nama):
        db = self._connect()
        affectedRow = db.execute(
            "DELETE FROM daftarbelanja WHERE nama=?", (nama,)
        ).rowcount
        self._disconnect(db)
        if affectedRow <= 0:
            raise NotFoundException(nama)

    def toggle(self, nama):
        db = self._connect()
        affectedRow = db.execute(
            "UPDATE daftarbelanja SET cek = 1 - cek WHERE nama=?", (nama,)
        ).rowcount
        if affectedRow <= 0:
            self._disconnect(db)
            raise NotFoundException(nama)

        row = db.execute(
            "SELECT nama, cek FROM daftarbelanja WHERE nama=?", (nama,)
        ).fetchone()
        self._disconnect(db)
        return Barang(nama=row[0], cek=(row[1] == 1))


db = Database()


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": "Layanan tidak ditemukan"},
    )


@app.exception_handler(NotFoundException)
def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": f"{exc.nama} tidak ditemukan"},
    )


@app.exception_handler(ServerException)
def not_found_handler(request: Request, exc: ServerException):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": exc.message},
    )


@app.get("/")
def redirect():
    return RedirectResponse(base_url + "/")


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
    db.delete(nama_barang)
    return {"status": "ok"}


@app.post(base_url + "/{nama_barang}")
def toggle_barang(nama_barang):
    return {"status": "ok", "item": db.toggle(nama_barang)}
