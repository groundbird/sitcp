### ToDo

- ファイル形式の仕様をつくる.
    + header に時刻や周波数, sample rate などを入れる
	+ csv
- sweep.py のオプションに `-f` (`--freq`) をとったとき, 指数表現で負の数 (e.g., -1e6 など) を使えるようにする. 現状は `-f 1e5 1e8` のように, いずれも正の数である場合か, `-f -1000 1000` のように指数表現を使わなければ指定できる.

### Issue

- `slowCtrl.wr_adc()` で任意の ADC レジスタを write して, `slowCtrl.rd_adc()` で ADC レジスタを read すると, address 00 が FF と表示される. もう一度 read すると 00 に戻っている.
