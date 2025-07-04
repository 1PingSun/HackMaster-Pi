class PasswordGenerator:
    def __init__(self, output_file='wordlist/identity_weak_passwords.txt'):
        self.output_file = output_file
        self.none_mean = ['123', '1234', '8888', '8787', '6666', '666', '168', '1111']
        self.special = ['!', '#', '$', '@', '']

    def append_to_file(self, text):
        if len(text) >= 8:
            with open(self.output_file, 'a') as f:
                f.write(text + '\n')

    def generate(self,
                DATE=[], # 今天日期、生日、重要日期等，以 yyyy-mm-dd 格式輸入
                TEL=[], # 手機號碼、市話等
                NAME=[], # 姓名、暱稱、組織名稱、組織縮寫等
                ID=[], # 身分證字號、統一編號等
                SSID='' # Wi-Fi SSID
                ):
        self.date = []
        for i in DATE:
            tmp_year = i.split('-')[0]
            tmp_month = i.split('-')[1]
            tmp_day = i.split('-')[2]
            self.date.append(f'{tmp_year}{tmp_month}{tmp_day}')
            self.date.append(f'{tmp_month}{tmp_day}{tmp_year}')
            self.date.append(f'{str(int(tmp_year) - 1911)}{tmp_month}{tmp_day}')
            self.date.append(f'{tmp_year}')
            self.date.append(f'{tmp_month}{tmp_day}')
        self.tel = []
        for i in TEL:
            self.tel.append(i)
            self.tel.append(i[2:])
        self.name = []
        for i in NAME:
            tmp_name = i.split(' ')
            self.name.append(''.join(tmp_name))
            self.name.append(''.join((i[0].upper() + i[1:].lower()) for i in tmp_name))
            self.name.append(''.join(i.lower() for i in tmp_name))
            self.name.append(''.join(i.upper() for i in tmp_name))
        self.id = []
        for i in ID:
            self.id.append(i)
            
        # ==============================
        
        for i in self.date:
            self.append_to_file(i)
        for i in self.tel:
            self.append_to_file(i)
        for i in self.id:
            self.append_to_file(i)
        for i in self.name:
            self.append_to_file(i)
        for i in self.special:
            for j in self.name:
                for k in self.date:
                    self.append_to_file(j + i + k)
                    self.append_to_file(k + i + j)
        for i in self.special:
            for j in self.name:
                for k in self.none_mean:
                    self.append_to_file(j + i + k)
                    self.append_to_file(k + i + j)
        self.append_to_file(SSID)
        
if __name__ == '__main__':
    generator = PasswordGenerator()
    generator.generate()