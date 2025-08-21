import asyncio
import random
from datetime import date
from datetime import datetime

class TCPServer:
    def __init__(self):
        self.num_answer_server = 0  # Счётчик ответов сервера
        self.dict_client = {}  # Словарь клиентов {id: (reader, writer)}
        self.keepalive_task = None  # Задача для отправки keepalive

    def write_file(self, listok):
        with open('log_server.txt', 'a', encoding='utf-8') as file:
            file.write(';'.join(str(item) for item in listok) + '\n')
    async def send_keepalive(self):
        """Отправляет keepalive сообщения всем подключенным клиентам каждые 5 секунд"""
        while True:
            await asyncio.sleep(5)
            if not self.dict_client:
                continue

            message = f"[{self.num_answer_server}] keepalive\n"
            self.num_answer_server += 1

            # Отправляем всем активным клиентам
            for client_id, (reader, writer) in list(self.dict_client.items()):
                try:
                    writer.write(message.encode())
                    await writer.drain()

                except ConnectionError:
                    print(f"Client {client_id} disconnected during keepalive")
                    del self.dict_client[client_id]

    def get_key(self, val):
        for key, value in self.dict_client.items():
            if val == value[1].get_extra_info('peername'):
                return key

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        client_id = len(self.dict_client) + 1
        self.dict_client[client_id] = (reader, writer)
        print(f"Подключился клиент {client_id}: {addr}")

        try:
            while True:
                list_log = []
                data = await reader.read(1024)
                if not data:
                    break

                message = data.decode().strip()
                list_log.append(str(date.today()))
                list_log.append(str(datetime.now().time()))
                list_log.append(str(message[:-1]))
                print(f"{client_id}: {message}")

                # 90% вероятность ответа
                if random.choices([True, False], weights=[0.9, 0.1])[0]:
                    time_sleep = random.uniform(0.1, 1)
                    await asyncio.sleep(time_sleep)

                    num_ask_server = message.split(']')[0][1:]  # Извлекаем номер запроса клиента
                    response = f"[{self.num_answer_server}/{num_ask_server}] PONG ({client_id})\n"
                    list_log.append(str(date.today()))
                    list_log.append(str(datetime.now().time()))
                    list_log.append(str(response))
                    self.num_answer_server += 1

                    writer.write(response.encode())
                    await writer.drain()
                else: list_log.append('Проигнорировано')
                self.write_file(list_log)
        except ConnectionError:
            print(f"Клиент {client_id} отключился неожиданно")
        finally:
            print(f"Отключение клиента {client_id}")
            if client_id in self.dict_client:
                del self.dict_client[client_id]
            writer.close()
            await writer.wait_closed()


async def main():
    server = TCPServer()

    # Запускаем задачу keepalive в фоне
    server.keepalive_task = asyncio.create_task(server.send_keepalive())

    tcp_server = await asyncio.start_server(
        server.handle_client,
        '127.0.0.1',
        8889
    )
    addr = tcp_server.sockets[0].getsockname()
    print(f"Сервер запущен на {addr}")

    try:
        async with tcp_server:
            await tcp_server.serve_forever()
    except asyncio.CancelledError:
        pass
    finally:
        server.keepalive_task.cancel()
        await server.keepalive_task


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Сервер остановлен")