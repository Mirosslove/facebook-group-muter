# -*- coding: utf-8 -*-
"""
Скрипт для автоматического отключения уведомлений от групп в Facebook.

ВНИМАНИЕ: Facebook не одобряет автоматизацию. Использование этого скрипта
может привести к временной или постоянной блокировке вашего аккаунта.
Используйте его на свой страх и риск. У меня лично было все - ОК
"""
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ ---

# 1. Укажите здесь ПОЛНЫЙ путь к файлу chromedriver.exe, который вы скачали.
#    Пример для Windows: r"C:\Users\User\Downloads\chromedriver-win64\chromedriver.exe"
#    Пример для macOS: r"/Users/User/Downloads/chromedriver-mac-arm64/chromedriver"
#    Важно: буква 'r' перед кавычками должна остаться!
CHROME_DRIVER_PATH = r"ПУТЬ_К_ВАШЕМУ_ФАЙЛУ_chromedriver.exe"

# 2. URL страницы со списком ваших групп. Найдите свой, если этот не работает.
#    Сортировка по дате добавления делает список более стабильным для скрипта.
GROUPS_URL = "https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added"

# 3. Название папки для хранения профиля Chrome.
#    Это позволяет не входить в аккаунт каждый раз. Папка будет создана рядом со скриптом.
PROFILE_FOLDER_NAME = "chrome_profile"

# --- КОНЕЦ НАСТРОЕК ---


def setup_driver():
    """Настраивает и запускает WebDriver с нужными опциями."""
    options = webdriver.ChromeOptions()
    # Отключаем всплывающие окна с запросом на показ уведомлений от сайтов
    options.add_argument("--disable-notifications")
    # Устанавливаем язык интерфейса, чтобы названия кнопок были предсказуемыми
    options.add_argument("--lang=uk-UA,en-US")
    # Указываем путь к папке с профилем для сохранения сессии
    profile_path = os.path.join(os.getcwd(), PROFILE_FOLDER_NAME)
    options.add_argument(f"user-data-dir={profile_path}")

    service = Service(executable_path=CHROME_DRIVER_PATH)
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print("="*60)
        print("!!! КРИТИЧЕСКАЯ ОШИБКА: Не удалось запустить WebDriver. !!!")
        print("Пожалуйста, проверьте следующие моменты:")
        print(f"1. Правильно ли указан путь к драйверу в CHROME_DRIVER_PATH?")
        print(f"   Текущий путь: {CHROME_DRIVER_PATH}")
        print("2. Соответствует ли версия вашего ChromeDriver версии браузера Chrome?")
        print(f"Ошибка Selenium: {e}")
        print("="*60)
        return None
    return driver

def main():
    """Основная функция скрипта."""
    print("--- Запуск Facebook Group Muter v7.1 ---")
    driver = setup_driver()
    if not driver:
        input("Нажмите Enter для выхода.")
        return

    driver.get(GROUPS_URL)
    driver.maximize_window()

    print("\n" + "="*60)
    print("ВАШИ ДЕЙСТВИЯ:")
    print("1. В открывшемся окне браузера войдите в свой аккаунт Facebook.")
    print("   (Если вы уже входили ранее, сессия может сохраниться).")
    print("2. Дождитесь полной загрузки страницы с вашими группами.")
    print("3. Вернитесь в это окно и нажмите Enter, чтобы начать.")
    print("="*60)
    input("Нажмите Enter для продолжения...")

    wait = WebDriverWait(driver, 15)

    try:
        print("\n--- Начало работы ---")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='main']")))
        print("[1/4] Страница с группами загружена.")

        print("[2/4] Прокручиваю страницу до конца, чтобы найти все группы...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Пауза, чтобы дать контенту подгрузиться
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("      Достигнут конец списка.")
                break
            last_height = new_height

        # Селектор для поиска "карточек" групп. Он ищет блок, в котором есть
        # и ссылка на группу, и кнопка "Більше" (или "More" для английского интерфейса).
        xpath_selector = "//div[.//a[contains(@href, '/groups/') and @role='link'] and .//div[contains(@aria-label, 'Більше') or contains(@aria-label, 'More')]]"
        all_group_cards = driver.find_elements(By.XPATH, xpath_selector)

        if not all_group_cards:
            print("\n[!] Не найдено ни одной карточки группы на странице. Возможно, Facebook изменил верстку.")
            return

        total_groups = len(all_group_cards)
        print(f"[3/4] Найдено карточек для обработки: {total_groups}.")
        print("[4/4] Начинаю процесс отключения уведомлений...")
        print("-" * 60)

        processed_count = 0
        for i in range(total_groups):
            # На каждой итерации ищем элементы заново, чтобы избежать ошибок "устаревшего" элемента
            current_cards = driver.find_elements(By.XPATH, xpath_selector)
            if i >= len(current_cards):
                break
            
            card = current_cards[i]
            group_name = f"Группа #{i+1}"  # Имя по умолчанию

            try:
                # Пытаемся получить реальное имя группы для красивого лога
                group_name_element = card.find_element(By.XPATH, ".//a[contains(@href, '/groups/') and @role='link']//span")
                if group_name_element.text.strip():
                    group_name = group_name_element.text

                print(f"--- Обработка {i+1}/{total_groups}: '{group_name}' ---")

                # Прокручиваем к элементу, чтобы он был в поле зрения
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", card)
                time.sleep(0.5)

                # Имитируем наведение мыши, чтобы появилась кнопка
                webdriver.ActionChains(driver).move_to_element(card).perform()
                time.sleep(0.5)

                # Нажимаем кнопку "..." ("Більше")
                more_button = card.find_element(By.XPATH, ".//div[contains(@aria-label, 'Більше') or contains(@aria-label, 'More')]")
                more_button.click()
                print("      > Нажал 'Більше'...")

                # Нажимаем "Управлять уведомлениями"
                manage_notif_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='menuitem']//span[text()='Керувати сповіщеннями']")))
                manage_notif_button.click()
                print("      > Нажал 'Керувати сповіщеннями'...")

                # В диалоговом окне выбираем "Выключить"
                off_radio_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//div[@aria-label='Вимк.']")))
                off_radio_button.click()
                print("      > Выбрал 'Вимк.'...")

                # Нажимаем "Сохранить"
                save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Зберегти' or @aria-label='Сохранить' or @aria-label='Save']")))
                save_button.click()
                print("      [✓] Успешно сохранено!")
                processed_count += 1

                time.sleep(random.uniform(2, 4)) # Случайная пауза, чтобы быть похожим на человека

            except (NoSuchElementException, TimeoutException):
                print(f"      [i] Не удалось выполнить действие. Вероятно, уведомления уже выключены.")
                continue
            except Exception as e:
                print(f"      [!] Произошла непредвиденная ошибка: {type(e).__name__}. Пропускаю группу.")
                # Если что-то пошло не так, лучше попытаться закрыть всплывающее окно
                try:
                    close_button = driver.find_element(By.XPATH, "//div[@aria-label='Закрити' or @aria-label='Close']")
                    close_button.click()
                    time.sleep(1)
                except:
                    # Если не получилось, просто обновляем страницу
                    driver.refresh()
                    time.sleep(3)
                continue

    except TimeoutException:
        print("\n[!] Ошибка: Страница не загрузилась за 15 секунд. Проверьте интернет-соединение.")
    except Exception as e:
        print(f"\n[!] Произошла критическая ошибка во время выполнения: {e}")
    finally:
        print("\n" + "="*60)
        print("--- РАБОТА ЗАВЕРШЕНА ---")
        if 'processed_count' in locals():
            print(f"Успешно обработано групп в этой сессии: {processed_count}")
        print("Рекомендуется запустить скрипт еще раз, чтобы обработать группы,")
        print("которые могли быть пропущены из-за случайных ошибок загрузки.")
        print("="*60)
        input("Нажмите Enter для выхода.")
        if 'driver' in locals() and driver:
            driver.quit()

if __name__ == "__main__":
    main()