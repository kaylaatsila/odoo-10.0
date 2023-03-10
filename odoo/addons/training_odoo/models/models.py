# -*- coding: utf-8 -*-

from odoo import exceptions, models, fields, api
from datetime import timedelta

# class training_odoo(models.Model):
#     _name = 'training_odoo.training_odoo'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class Kursus(models.Model):
    _name = 'training.kursus'

    name = fields.Char(string="Judul", required=True)
    description = fields.Text()
    session_ids = fields.One2many('training.sesi', 'course_id', string="Sesi")
    responsible_id = fields.Many2one(
        'res.users', ondelete='set null', string="Penanggung Jawab", index=True)
    attendee_ids = fields.Many2many('res.partner', string="Peserta")

    _sql_constraints = [
        ('name_description_cek', 'CHECK(name != description)',
         'Judul kursus dan keterangan tidak boleh sama '),
        ('name_unik', 'UNIQUE(name)', 'Judul kursus harus unik')
    ]

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        # Searching judul kursus yang sama dan menyimpannya pada variable copied_count
        copied_count = self.search_count(
            [('name', '=like', "Copy of {}%".format(self.name))])

        if not copied_count:  # Cek isi variable copied_count (hasil searching)
            # Jika proses searching judul yang sama tidak ditemukan, maka judul baru akan dikasih imbuhan 'Copy of'
            new_name = "Copy of {}".format(self.name)
        else:
            # Jika proses searching judul yang sama ditemukan, maka judul baru akan dikasih imbuhan 'Copy of' dan angka terakhir duplicate
            new_name = "Copy of {} ({})".format(self.name, copied_count)

        # Mereplace value field name dengan yang sudah di sesuaikan
        default['name'] = new_name
        return super(Kursus, self).copy(default)


class Sesi(models.Model):
    _name = 'training.sesi'

    name = fields.Char(required=True)
    start_date = fields.Date()
    duration = fields.Float(digits=(6, 2), help="Durasi Hari")
    seats = fields.Integer(string="Jumlah Kursi")
    instructor_id = fields.Many2one('res.partner', string="Instruktur", domain=[
                                    '|', ('instructor', '=', True), ('category_id.name', 'ilike', "Pengajar")])
    attendee_ids = fields.Many2many('res.partner', string="Peserta", domain=[
                                    ('instructor', '=', False)])
    course_id = fields.Many2one(
        'training.kursus', ondelete='cascade', string="Kursus", required=True)
    responsible_id = fields.Many2one(
        'res.users', ondelete='set null', string="Penanggung Jawab", index=True)

    taken_seats = fields.Float(string="Kursi Terisi", compute='_taken_seats')

    attendees_count = fields.Integer(string="Jumlah Peserta", compute='_get_attendees_count', store=True)
  
    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            # Mengupdate field attendees_count berdasarkan jumlah record di tabel peserta 
            r.attendees_count = len(r.attendee_ids)
            
    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        # cek nilai field seats, jika dibawah 0 (negatif), maka masuk kondisi if
        if self.seats <= 0:
            return {
                'value': {'seats': len(self.attendee_ids) or 1  # mengisi field seats dengan nilai jumlah peserta atau 1
                          },
                'warning': {'title': "Nilai Jumlah Kursi Salah",  # judul pop up
                            'message': "Jumlah Kursi Tidak Boleh Negatif"  # pesan pop up
                            }
            }

        # cek nilai field seats (jumlah kursi) apakah lebih kecil dari field attendee_ids (jumlah peserta), jika iya maka masuk kondisi if
        if self.seats < len(self.attendee_ids):
            return {
                'value': {'seats': len(self.attendee_ids)  # mengisi field seats dengan nilai jumlah peserta
                          },
                'warning': {'title': "Peserta Terlalu Banyak",  # judul pop up
                                     'message': "Tambahkan Kursi atau Kurangi Peserta"  # pesan pop up
                            }
            }

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            # Jika field instructor_id (Instruktur) diisi DAN instructor_id ada di tabel attendee_ids (Peserta), maka munculkan pesan error
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError(
                    "Seorang instruktur tidak boleh menjadi peserta")

    end_date = fields.Date(string="Tanggal Selesai", store=True,
                           compute='_get_end_date', inverse='_set_end_date')

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            # Pengecekan jika field duration & start_date tidak diisi, maka field end_date akan di update sama seperti field start_date
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Membuat variable start yang isinya tanggal dari field start_date
            start = fields.Datetime.from_string(r.start_date)

            # Membuat variable duration yang isinya durasi hari dari field duration
            # Durasi hari dikurangi 1 detik agar start_date masuk kedalam durasi hari
            duration = timedelta(days=r.duration, seconds=-1)

            # Mengupdate field end_date dari perhitungan variabel start ditambah variabel duration
            r.end_date = start + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Membuat variable start_date yang isinya tanggal dari field start_date
            start_date = fields.Datetime.from_string(r.start_date)

            # Membuat variable end_date yang isinya tanggal dari field end_date
            end_date = fields.Datetime.from_string(r.end_date)

            # Mengupdate field duration (jika ada perubahan dari field end_date) dari perhitungan variabel end_date dikurangi variabel start_date (ditambah 1 hari agar end_date termasuk durasi hari)
            r.duration = (end_date - start_date).days + 1
