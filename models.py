# encoding:utf-8
import peewee

db = peewee.SqliteDatabase("cpu.db")

#定义数据表
class CPU(peewee.Model):
    model = peewee.CharField(max_length = 32)
    model_name = peewee.CharField(max_length = 32)
    stepping = peewee.CharField(max_length = 32)
    microcode = peewee.CharField(max_length = 32)
    cpu_MHz = peewee.CharField(max_length = 32)

    # 关联数据库和表
    class Meta:
        database = db

if __name__ == "__main__":
    CPU.create_table()