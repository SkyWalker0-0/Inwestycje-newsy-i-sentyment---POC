# Inwestycje-newsy-i-sentyment---POC

## Opis projektu
Celem projektu było sprawdzenie, czy dane newsowe dotyczące Bitcoina oraz ich sentyment mogą zostać połączone z danymi rynkowymi BTC w taki sposób, aby wspierać proces podejmowania decyzji inwestycyjnych.

Projekt ma charakter **Proof of Concept** i koncentruje się na eksploracyjnej analizie danych (**EDA**). Główna idea polegała na zestawieniu:
- danych rynkowych Bitcoina,
- liczby publikowanych newsów,
- sentymentu wiadomości,
- oraz reakcji rynku mierzonej stopą zwrotu i zmiennością.

Analiza miała odpowiedzieć na pytanie, czy sam sentyment nagłówków newsów może być użytecznym sygnałem inwestycyjnym, czy też większą wartość ma ogólna aktywność informacyjna rynku.

---

## Cel projektu
Głównym celem projektu było:
1. pobranie i przygotowanie danych rynkowych BTC,
2. pobranie i oczyszczenie danych newsowych,
3. połączenie obu źródeł danych w jeden zbiór analityczny,
4. przeprowadzenie EDA,
5. sprawdzenie, czy istnieją zależności pomiędzy:
   - sentymentem newsów a stopą zwrotu BTC,
   - liczbą newsów a zmiennością ceny BTC,
   - sentymentem z danego dnia a zachowaniem rynku w dniu następnym.

---

## Zakres analizy
Projekt obejmuje dwa główne obszary:

### 1. EDA rynku Bitcoin
W tej części przeanalizowano:
- cenę zamknięcia BTC w czasie,
- dzienne stopy zwrotu,
- rozkład zmian ceny,
- wartości odstające,
- 30-dniową zmienność,
- wolumen obrotu,
- korelacje pomiędzy podstawowymi zmiennymi rynkowymi.

### 2. EDA newsów i sentymentu
W tej części przeanalizowano:
- liczbę newsów w czasie,
- źródła publikacji,
- średni sentyment,
- udział pozytywnych i negatywnych newsów,
- zależność między liczbą newsów a zmiennością BTC,
- zależność między udziałem pozytywnych/negatywnych newsów a stopą zwrotu BTC,
- zależność między sentymentem z danego dnia a stopą zwrotu BTC w następnym dniu.

---

## Źródła danych
W projekcie wykorzystano dwa główne źródła danych:

- **yfinance** — dane rynkowe Bitcoina (BTC-USD),
- **Alpha Vantage News & Sentiment API** — dane newsowe wraz z oceną sentymentu.

---

## Wykorzystane technologie i biblioteki
Projekt został zrealizowany w Pythonie, głównie w formie notebooka Jupyter.

Wykorzystane biblioteki:
- `pandas`
- `numpy`
- `matplotlib`
- `scipy`
- `yfinance`
- `requests`

Dodatkowo w projekcie wykorzystywano własne moduły pomocnicze do ładowania i przygotowania danych, między innymi:
- `btc_loader`
- `news_loader`

---

## Opis modułów pomocniczych

### `news_loader.py`
Moduł `news_loader` odpowiada za pobieranie, wczytywanie, czyszczenie i aktualizację danych newsowych dotyczących Bitcoina. Zawiera funkcje do pracy z plikiem CSV oraz do komunikacji z API Alpha Vantage. :contentReference[oaicite:0]{index=0}

#### Najważniejsze funkcje:
- `empty_news_df()`  
  Tworzy pusty DataFrame z ustaloną strukturą kolumn dla newsów.

- `load_existing_news(csv_path)`  
  Wczytuje istniejący plik CSV z newsami. Jeśli plik nie istnieje albo jest pusty, zwraca pusty DataFrame o poprawnej strukturze.

- `clean_news_df(df, min_date="2026-01-01")`  
  Czyści dane newsowe poprzez:
  - uzupełnienie brakujących kolumn,
  - konwersję dat,
  - usunięcie rekordów z brakującą datą publikacji, tytułem lub źródłem,
  - odfiltrowanie rekordów starszych niż zadana data,
  - pozostawienie newsów powiązanych z Bitcoinem,
  - usunięcie duplikatów,
  - posortowanie danych po czasie publikacji.  
  Funkcja ta przygotowuje dane do dalszej analizy. 

- `fetch_news_from_api(api_key, time_from, time_to=None, limit=1000)`  
  Pobiera newsy z API Alpha Vantage dla wskazanego zakresu czasu. Funkcja obsługuje również sytuacje błędne, takie jak limit API, błędne parametry zapytania lub brak pola `feed` w odpowiedzi. 

- `transform_feed_to_df(feed)`  
  Zamienia surową odpowiedź API w uporządkowany DataFrame zawierający najważniejsze pola, takie jak data publikacji, tytuł, źródło, link oraz sentyment.

- `fetch_news_for_window(api_key, start_dt, end_dt)`  
  Pobiera dane newsowe dla konkretnego przedziału czasowego i zamienia je na DataFrame.

- `build_initial_news_csv(api_key, csv_path="btc_news.csv", start_date="2026-01-01")`  
  Buduje początkowy plik CSV z newsami, pobierając dane etapami miesiąc po miesiącu. Następnie łączy dane, czyści je i zapisuje do pliku. Funkcja została przygotowana tak, aby nie nadpisywać istniejącego poprawnego pliku pustymi danymi. 

- `update_news_csv(api_key, csv_path="btc_news.csv", min_date="2026-01-01")`  
  Aktualizuje istniejący plik CSV tylko o nowe rekordy od ostatniej zapisanej daty. Dzięki temu możliwe jest inkrementalne rozszerzanie zbioru danych bez ponownego pobierania całej historii. 

---

### `btc_loader.py`
Moduł `btc_loader` odpowiada za pobieranie danych rynkowych BTC z biblioteki `yfinance` dla dokładnie tego samego okresu, który występuje w danych newsowych. Dzięki temu możliwe jest późniejsze poprawne połączenie obu źródeł danych w jednej analizie. :contentReference[oaicite:5]{index=5}

#### Najważniejsza funkcja:
- `load_btc_for_news_period(news_df, force_interval=None)`  
  Funkcja:
  - odczytuje minimalną i maksymalną datę z danych newsowych,
  - na tej podstawie wyznacza zakres pobierania danych BTC,
  - automatycznie dobiera interwał danych (`1h` lub `1d`) w zależności od długości analizowanego okresu,
  - pobiera dane `BTC-USD` z `yfinance`,
  - normalizuje strukturę kolumn,
  - sprawdza obecność wymaganych pól (`Datetime`, `Close`, `High`, `Low`, `Open`, `Volume`),
  - oblicza dodatkowe zmienne analityczne:
    - `Return` — procentową stopę zwrotu,
    - `Range` — zakres zmian ceny,
    - `time_key` — klucz czasowy do późniejszego łączenia z newsami,
    - `btc_interval` — użyty interwał danych. :contentReference[oaicite:6]{index=6}

Moduł ten pełni więc rolę warstwy pobierającej i przygotowującej dane rynkowe do dalszej analizy EDA oraz do łączenia z agregatami newsowymi. :contentReference[oaicite:7]{index=7}

---

## Struktura analizy
Notebook obejmuje następujące etapy:

### 1. Pobranie danych BTC
Pobranie historycznych danych rynkowych dla pary `BTC-USD`, a następnie przygotowanie podstawowych kolumn analitycznych, takich jak:
- `Return` — dzienna stopa zwrotu,
- `Range` — zakres zmian ceny,
- zmienne pomocnicze związane ze zmiennością i agregacją czasową.

### 2. EDA danych BTC
W tej części wykonano wizualizacje i analizy opisowe dotyczące:
- trendu cenowego,
- zmienności rynku,
- rozkładu stóp zwrotu,
- wolumenu,
- korelacji pomiędzy zmiennymi.

### 3. Pobranie i przygotowanie newsów
Dane newsowe zostały pobrane z API i zapisane do pliku. Następnie wykonano:
- czyszczenie danych,
- konwersję dat,
- porządkowanie rekordów,
- analizę źródeł i zakresu czasowego,
- przygotowanie danych do połączenia z cenami BTC.

### 4. Łączenie newsów z danymi rynkowymi
Na tym etapie połączono dane newsowe z danymi cenowymi, tworząc wspólny zbiór do analizy zależności pomiędzy informacjami z rynku medialnego a zachowaniem ceny Bitcoina.

### 5. Analiza zależności
Sprawdzono między innymi:
- czy większa liczba newsów współwystępuje z większą zmiennością ceny BTC,
- czy większy udział pozytywnych newsów wiąże się z wyższą stopą zwrotu,
- czy większy udział negatywnych newsów wiąże się z niższą stopą zwrotu,
- czy sentyment z danego dnia wpływa na stopę zwrotu BTC w kolejnym dniu.

Do oceny zależności wykorzystano między innymi:
- analizę wizualną,
- korelację Spearmana,
- interpretację istotności statystycznej wyników.

---

## Najważniejsze wyniki
Najważniejsze obserwacje z projektu są następujące:

### 1. Rynek BTC charakteryzuje się wysoką zmiennością
Analiza danych rynkowych pokazała, że Bitcoin cechuje się:
- dużą zmiennością,
- częstym występowaniem silnych dziennych ruchów cenowych,
- obecnością wartości odstających,
- zmienną aktywnością inwestorów mierzoną wolumenem.

### 2. Sam sentyment newsów nie daje prostego sygnału inwestycyjnego
W analizowanym zbiorze nie potwierdzono istotnych zależności między:
- udziałem pozytywnych newsów a dzienną stopą zwrotu BTC,
- udziałem negatywnych newsów a dzienną stopą zwrotu BTC,
- sentymentem z danego dnia a stopą zwrotu BTC w dniu następnym.

Oznacza to, że prosty schemat:
- „więcej pozytywnych newsów = wzrost ceny”
- lub „więcej negatywnych newsów = spadek ceny”
nie znajduje potwierdzenia w wynikach tej analizy.

### 3. Liczba newsów była związana ze zmiennością rynku
Najbardziej wyraźnym rezultatem była dodatnia i statystycznie istotna zależność pomiędzy:
- **liczbą publikacji**
- a **zakresem zmian ceny BTC (Range)**

Sugeruje to, że intensywność napływu informacji może być użyteczna nie tyle do przewidywania kierunku ruchu ceny, lecz raczej do oceny poziomu aktywności, niepewności i ryzyka na rynku.

---

## Wniosek końcowy
Przeprowadzona analiza prowadzi do wniosku, że **sam sentyment nagłówków wiadomości nie stanowi wystarczającej podstawy do przewidywania kierunku zmian ceny Bitcoina**. Zarówno dla bieżącej dziennej stopy zwrotu, jak i dla stopy zwrotu w kolejnym dniu, nie zaobserwowano istotnych zależności między udziałem pozytywnych lub negatywnych newsów a zachowaniem rynku.

Jednocześnie analiza wykazała, że **liczba newsów jest istotnie związana ze zmiennością ceny BTC**, co oznacza, że dane informacyjne mogą być wartościowe jako element wspomagający ocenę sytuacji rynkowej.

W praktyce oznacza to, że:
- sentyment newsów nie powinien być traktowany jako samodzielny predyktor decyzji inwestycyjnych,
- ale dane newsowe mogą stanowić użyteczne uzupełnienie szerszego modelu analitycznego,
- zwłaszcza w połączeniu z takimi cechami jak zmienność, wolumen, historyczne stopy zwrotu czy liczba publikacji.

---

## Ograniczenia projektu
Projekt posiada kilka istotnych ograniczeń:

1. **Dane newsowe nie obejmują idealnie pełnych miesięcy**  
   Ze względu na ograniczenia API nie zawsze udało się pobrać kompletny i równomierny zakres newsów dla całego badanego okresu.

2. **Sentyment pochodzi z zewnętrznego źródła API**  
   Oznacza to, że jakość tej oceny zależy od metod zastosowanych przez dostawcę danych.

3. **Projekt ma charakter EDA / Proof of Concept**  
   Celem nie było zbudowanie gotowego modelu predykcyjnego, lecz sprawdzenie, które cechy danych są obiecujące z punktu widzenia dalszego rozwoju.

---

## Możliwe dalsze kierunki rozwoju
Projekt można rozwijać dalej między innymi poprzez:
- budowę modelu predykcyjnego lub klasyfikacyjnego,
- uwzględnienie opóźnień czasowych pomiędzy publikacją newsów a reakcją rynku,
- analizę jakości i wiarygodności źródeł,
- rozszerzenie zestawu cech o wolumen, zmienność historyczną i techniczne wskaźniki rynku,
- zastosowanie własnej analizy sentymentu zamiast gotowego score z API,
- testowanie modeli wspomagających decyzje inwestycyjne w szerszym ujęciu niż sam kierunek zmiany ceny.

---

## Charakter projektu
Projekt został przygotowany jako **Proof of Concept**, którego celem było sprawdzenie, czy połączenie danych rynkowych BTC z danymi newsowymi i sentymentem ma sens analityczny oraz czy może stanowić podstawę do budowy narzędzia wspierającego decyzje inwestycyjne.

Najważniejszy wniosek z projektu jest taki, że:
- **sentyment nagłówków sam w sobie okazał się zbyt słaby jako sygnał kierunku rynku,**
- natomiast **intensywność informacyjna rynku okazała się użyteczna w ocenie zmienności BTC.**