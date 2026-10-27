from datetime import datetime

def get_day_of_year():
    current_day = datetime.now()
    return current_day.timetuple().tm_yday


if __name__ == '__main__':
    print(get_day_of_year())