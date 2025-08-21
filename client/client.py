import asyncio
import sys
import random
from datetime import date, datetime
def write_file(listok):
    with open('log_client.txt', 'a', encoding='utf-8') as file:
        file.write(';'.join(str(item) for item in listok) + '\n')

async def tcp_client():
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8889)
        print("Успешное подключение к серверу")
        num_mes = 0

        while True:
            list_log_client = []
            time_sleep = random.uniform(0.3, 3)
            await asyncio.sleep(time_sleep)

            message = f'[{num_mes}] PING'
            num_mes += 1
            send_time = datetime.now()

            try:
                writer.write(message.encode())
                await writer.drain()

                list_log_client.extend([
                    send_time.date().isoformat(),
                    send_time.time().isoformat(timespec='milliseconds'),
                    message
                ])

                try:
                    data = await asyncio.wait_for(reader.read(100), timeout=1.0)
                    recv_time = datetime.now()
                    response = data.decode().strip()

                    if 'keepalive' in response:
                        list_log_client = [
                            recv_time.date().isoformat(),
                            '',  # Пустое время отправки
                            '',  # Пустой запрос
                            recv_time.time().isoformat(timespec='milliseconds'),
                            response
                        ]
                    else:
                        list_log_client.extend([
                            recv_time.time().isoformat(timespec='milliseconds'),
                            response
                        ])
                    write_file(list_log_client)
                    print(f"Ответ сервера: {response}")

                except asyncio.TimeoutError:
                    timeout_time = datetime.now()
                    list_log_client.extend([
                        timeout_time.time().isoformat(timespec='milliseconds'),
                        '(таймаут)'
                    ])
                    write_file(list_log_client)
                    print("Таймаут: сервер не ответил")

            except Exception as e:
                print(f"Ошибка при отправке/получении: {e}")
                break
    except ConnectionRefusedError:
        print("Ошибка: Сервер недоступен.")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        if 'writer' in locals():
            writer.close()
            await writer.wait_closed()
            print("Соединение закрыто")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(tcp_client())