from django.db.models.signals import pre_save, post_delete, pre_delete
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.dispatch import receiver
from django.conf import settings
from django.db import models
import unicodedata
import random
import string
import os

# Crear una cadena aleatoria de letras y numeros
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# cambiar nombre del archivo
def create_filename_path(filename, setname, sufix, length, lenghtrandom, strpath):
    ext = filename.split('.')[-1]
    texto_normalizado = unicodedata.normalize('NFD', setname)
    setname = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    setname = setname[:length] if len(setname) > length else setname
    random_string = generate_random_string(lenghtrandom)
    filename = f"{sufix}_{slugify(setname)}_{random_string}.{ext}"
    return os.path.join(strpath, filename)

# Funciones para enviar el archivo a su carpeta correspondiente
def set_imgDB_path(instance, filename):
    categoria = instance.categoria.categoria
    instanceTitulo = instance.titulo.strip().replace(' ', '')
    newName = f'{categoria}_{instanceTitulo}'
    thispath = os.path.join('imagenes/')
    if instance.categoria:
        if categoria == 'Mapa':
            thispath = os.path.join(thispath, 'mapa/')
        elif categoria == 'Calendario':
            thispath = os.path.join(thispath, 'calendario/')
    return create_filename_path(filename, newName, 'db', 35, 6, thispath)

def set_imgBlog_path(instance, filename):
    newName = instance.titulo.strip().replace(' ', '')
    thispath = os.path.join('imagenes/blogs/')
    return create_filename_path(filename, newName, 'blog', 18, 8, thispath)

def set_imgMarker_path(instance, filename):
    newName = instance.nombre.strip().replace(' ', '')
    thispath = os.path.join('imagenes/mapa/')
    return create_filename_path(filename, newName, 'marker', 18, 8, thispath)

def set_imgs_path(instance, filename):
    newName = filename.strip().replace(' ', '')
    theName, _  = os.path.splitext(newName)
    thispath = os.path.join('imagenes/')
    return create_filename_path(filename, theName, 'cross_image', 22, 11, thispath)

def set_conf_path(instance, filename):
    newName = filename.strip().replace(' ', '')
    theName, _  = os.path.splitext(newName)
    thispath = os.path.join('settings/')
    return create_filename_path(filename, theName, 'config', 16, 4, thispath)

def set_imgProfile_path(instance, filename):
    newName = instance.user.username.strip().replace(' ', '')
    thispath = os.path.join('imagenes/personal/')
    return create_filename_path(filename, newName, 'profile', 20, 8, thispath)

def set_pdfDB_path(instance, filename):
    newName = instance.titulo.strip().replace(' ', '')
    thispath = os.path.join('documentos/')
    return create_filename_path(filename, newName, 'db_doc', 18, 10, thispath)


class Categorias(models.Model):
    categoria = models.CharField(max_length=50)
    descripcion = models.TextField(null=True, blank=True)
    creacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.categoria
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

class Database(models.Model):
    categoria = models.ForeignKey(Categorias, on_delete=models.CASCADE, null=True)
    titulo = models.CharField(max_length=200)
    informacion = models.TextField(blank=True, null=True)
    redirigir = models.TextField(blank=True, null=True)
    frecuencia = models.IntegerField(default=0)
    documento = models.FileField(upload_to=set_pdfDB_path, max_length=120, blank=True, null=True)
    imagen = models.ImageField(upload_to=set_imgDB_path, max_length=120, blank=True, null=True)
    tags = models.TextField(blank=True, null=True, help_text='Palabras Clave. Separar por comas')
    uuid = models.CharField(max_length=25)
    evento_fecha_inicio = models.DateTimeField(blank=True, null=True)
    evento_fecha_fin = models.DateTimeField(blank=True, null=True)
    evento_allDay = models.BooleanField(default=False)
    evento_lugar = models.CharField(max_length=200, blank=True, null=True, default='Campus UTC')
    evento_className = models.CharField(max_length=100, blank=True, null=True, default='event_detail')
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def get_tag_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def __str__(self):
        return self.titulo
    
    def delete(self, *args, **kwargs):
        if self.imagen:
            self.imagen.delete()
        if self.documento:
            self.documento.delete()
        super(Database, self).delete(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_info = Database.objects.get(pk=self.pk)
            if old_info.imagen and old_info.imagen != self.imagen:
                old_info.imagen.delete(save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Base de Datos"
        verbose_name_plural = "Bases de Datos"

class Mapa(models.Model):
    uuid = models.CharField(max_length=25, unique=True)
    nombre = models.CharField(max_length=200)
    informacion = models.TextField()
    color = models.CharField(max_length=50)
    coords = models.TextField(blank=True, null=True, help_text='Coordenadas JSON del mapa')
    door = models.CharField(max_length=255, blank=True, null=True, help_text='Coordenadas de la puerta separadas por comas')
    tags = models.TextField(blank=True, null=True, help_text='Palabras Clave. Separar por comas')
    is_marker = models.BooleanField(default=False, help_text='Para los marcadores de imagen')
    hide_name = models.BooleanField(default=False)
    size_marker = models.CharField(max_length=4, default='0.05')
    otheraction = models.TextField(blank=True, null=True, help_text='Acciones adicionales')
    
    def get_tag_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Mapa"
        verbose_name_plural = "Mapa"

class galeria(models.Model):
    imagen = models.ImageField(upload_to=set_imgs_path, max_length=120, blank=True, null=True)
    uuid = models.ForeignKey(Mapa, to_field='uuid', on_delete=models.CASCADE, null=True, blank=True)
    usos = models.TextField(blank=True,null=True)
    
    def __str__(self):
        return self.imagen.name
    
    def delete(self, *args, **kwargs):
        if self.imagen:
            self.imagen.delete()
        super(galeria, self).delete(*args, **kwargs)
    
    class Meta:
        verbose_name = "Galeria"
        verbose_name_plural = "Galerias"

class Preguntas(models.Model):
    pregunta = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
    
class Configuraciones(models.Model):
    qr_image = models.FileField(upload_to='settings/', max_length=200)
    qr_button = models.BooleanField(default=True)
    calendar_btnsYear = models.BooleanField(default=True)
    copyright_year = models.CharField(max_length=50, default='2020')
    utc_link = models.TextField()
    redes_sociales = models.TextField(blank=True, null=True)
    about_img_first = models.ImageField(upload_to=set_conf_path, max_length=200)
    about_img_second = models.ImageField(upload_to=set_conf_path, max_length=200)
    about_text_first = models.TextField()
    about_text_second = models.TextField()
    
    def __str__(self):
        return self.copyright_year
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_images = Configuraciones.objects.get(pk=self.pk)
            if old_images.qr_image and old_images.qr_image != self.qr_image:
                old_images.qr_image.delete(save=False)
            if old_images.about_img_first and old_images.about_img_first != self.about_img_first:
                old_images.about_img_first.delete(save=False)
            if old_images.about_img_second and old_images.about_img_second != self.about_img_second:
                old_images.about_img_second.delete(save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Configuracion"
        verbose_name_plural = "Configuraciones"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=set_imgProfile_path, max_length=120, blank=True, null=True)
    tutorial = models.BooleanField(default=True)
    blog_firma = models.CharField(max_length=200 ,blank=True, null=True)
    password_update = models.DateField(blank=True, null=True)
    user_token = models.TextField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_profile = UserProfile.objects.get(pk=self.pk)
            if old_profile.profile_picture and old_profile.profile_picture != self.profile_picture:
                old_profile.profile_picture.delete(save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

# Función genérica para eliminar archivos
def delete_files(instance, fields):
    for field in fields:
        file = getattr(instance, field, None)
        if file:
            file.delete(save=False)

# Señal para eliminar archivos antes de eliminar el objeto
@receiver(pre_delete, sender=Database)
@receiver(pre_delete, sender=galeria)
def delete_files_on_object_delete(sender, instance, **kwargs):
    fields_to_delete = {
        Database: ['imagen', 'documento'],
        galeria: ['imagen'],
    }
    delete_files(instance, fields_to_delete[sender])


@receiver(post_delete, sender=UserProfile)
def delete_profile_picture_on_delete(sender, instance, **kwargs):
    if instance.profile_picture:
        instance.profile_picture.delete(save=False)
