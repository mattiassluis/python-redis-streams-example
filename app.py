import argparse
import asyncio
from random import randint

import aioredis


async def consumer(loop, channels=None, name=None):
    await asyncio.sleep(randint(1, 60)/10)
    print(f'Started consumer {name}', flush=True)
    redis = await aioredis.create_redis('redis://redis', loop=loop)
    events = {}
    for channel in channels:
        events[channel] = {
            'last': None,
            'data': []
        }
        history = await redis.xrange(channel)
        for item in history:
            print(f'{name}: history [{channel}] {item[1]}', flush=True)
            events[channel]['data'].append(item[1])
            events[channel]['last'] = item[0]

    await asyncio.sleep(5)

    while True:
        items = await redis.xread(channels, latest_ids=[events[x]['last'] or '0' for x in channels])
        for item in items:
            channel = item[0].decode()
            print(f'{name}: received [{channel}] {item[2]}', flush=True)
            events[channel]['data'].append(item[2])
            events[channel]['last'] = item[1]


async def producer(loop, channel=None, name=None):
    print(f'Started producer {name}', flush=True)
    i = 0
    redis = await aioredis.create_redis('redis://redis', loop=loop)
    while True:
        fields = {b'name': name.encode(), b'time': str(i).encode()}
        print(f'{name}[{channel}]: {i}', flush=True)
        i += 1
        await redis.xadd(channel, fields)
        await asyncio.sleep(randint(1, 30)/10)


def main():
    loop = asyncio.get_event_loop()
    args = _parse_args()
    channels = [x.strip() for x in args.channels.split(',')]

    if args.role == 'consumer':
        loop.run_until_complete(consumer(loop, channels, name=args.name))
    else:
        loop.run_until_complete(producer(loop, channels[0], name=args.name))


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', help='Role', default='consumer')
    parser.add_argument('--channels', help='Channels', default='default')
    parser.add_argument('--name', help='Name')
    return parser.parse_args()


if __name__ == '__main__':
    main()
