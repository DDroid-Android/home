def get_time(pair) -> int:
    return pair[0] * 60 + pair[1]


def get_total_time(array):
    total_time = sum(list(map(get_time, array))) / 5
    print(f"{int(total_time / 60)}m{int(total_time) % 60}s")


if __name__ == "__main__":
    
    wp_10302 = [(0, 51), (0, 50), (1, 0), (1, 19), (2, 17)]
    get_total_time(wp_10302)

    sf_239 = [(2, 15), (2, 14), (2, 11), (1, 25), (2, 15)]
    get_total_time(sf_239)

    anki_4977 = [(5, 0), (5, 47), (3, 29), (6, 22), (1, 41)]
    get_total_time(anki_4977)

    on_745 = [(6, 52), (6, 42), (4, 56), (8, 33), (2, 16)]
    get_total_time(on_745)

    anki_4451 = [(6, 57), (8, 53), (6, 29), (9, 37), (7, 27)]
    get_total_time(anki_4451)

