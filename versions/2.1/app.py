#!/usr/bin/env python3
import os, sys, shutil, subprocess, pathlib, json
from gi.repository import Gtk, Gio, GLib, Gdk
HOME=pathlib.Path.home()
APP='Gestion de stockage'
CONFIG=HOME/'.config/gestion-stockage-final/beta-2.1/settings.json'
CSS_BASE = """
window, window.background, .app-root { background-color: BG; color: FG; }
.sidebar { background-color: SIDE; border-right: 1px solid BORDER; padding: 14px; min-width: 210px; }
.content-area { background-color: BG; color: FG; }
.sidebar button { min-height: 42px; border-radius: 12px; margin: 2px; }
.sidebar button:hover { background-color: HOVER; }
.primary-action { background-color: ACCENT; color: white; border-radius: 12px; font-weight: 700; min-height: 42px; }
.danger-action { color: #e35a65; }
.heading { font-size: 23px; font-weight: 800; margin-bottom: 8px; }
list, listbox, scrolledwindow, viewport { background-color: BG; color: FG; }
list row, listbox row { border-radius: 9px; margin: 2px; }
list row:selected, listbox row:selected { background-color: HOVER; }
progressbar trough { min-height: 16px; border-radius: 10px; }
progressbar progress { background-color: ACCENT; border-radius: 10px; }
"""
PALETTES = {
 'blue':'#287df0', 'purple':'#8059e8', 'green':'#168a70', 'cyan':'#078aaf'
}

class Window(Gtk.ApplicationWindow):
 def __init__(self,app):
  super().__init__(application=app,title=APP,default_width=1120,default_height=720)
  self.entries=[]
  try: self.prefs=json.loads(CONFIG.read_text())
  except (OSError,ValueError,TypeError): self.prefs={}
  self.theme=self.prefs.get('theme','system')
  if self.theme not in ('system','dark','light'):self.theme='system'
  self.accent=self.prefs.get('accent','blue')
  if self.accent not in PALETTES:self.accent='blue'
  self.cwd=pathlib.Path(self.prefs.get('start_dir',str(HOME))).expanduser()
  if not self.cwd.is_dir():self.cwd=HOME
  self.show_hidden=bool(self.prefs.get('show_hidden',False))
  self.css=Gtk.CssProvider()
  self.restyle()
  Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),self.css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
  self.apply_theme()
  root=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL);root.add_css_class('app-root'); self.set_child(root)
  sidebar=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); sidebar.set_margin_top(20); sidebar.set_margin_start(12); sidebar.set_margin_end(12); sidebar.add_css_class('sidebar'); root.append(sidebar)
  title=Gtk.Label(label='💠  Gestion de stockage'); title.add_css_class('title-3'); sidebar.append(title)
  for name,callback in [('🏠  Accueil',self.home),('📁  Fichiers',self.files),('🎮  Jeux & applis',self.games),('🧹  Nettoyage',self.clean),('⚙️  Paramètres',self.settings_page)]:
   b=Gtk.Button(label=name); b.connect('clicked',lambda _b,f=callback:f()); sidebar.append(b)
  sidebar.append(Gtk.Separator())
  self.theme_button=Gtk.Button(); self.theme_button.connect('clicked',self.toggle_theme); sidebar.append(self.theme_button); self.update_theme_label()
  self.content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); self.content.set_margin_top(18); self.content.set_margin_bottom(18); self.content.set_margin_start(20); self.content.set_margin_end(20); self.content.set_hexpand(True); self.content.add_css_class('content-area'); root.append(self.content)
  self.home()
 def clear(self):
  while child:=self.content.get_first_child():self.content.remove(child)
 def heading(self,text):
  label=Gtk.Label(label=text,xalign=0);label.add_css_class('heading');self.content.append(label)
 def info(self,text):
  label=Gtk.Label(label=text,xalign=0,wrap=True);self.content.append(label)
 def btn(self,container,label,callback):
  b=Gtk.Button(label=label);b.connect('clicked',callback);container.append(b);return b
 def dialog(self,title,message,action=None,destructive=False):
  d=Gtk.AlertDialog();d.set_message(title);d.set_detail(message);d.set_buttons(['Annuler','Confirmer'] if action else ['OK']);d.set_cancel_button(0);d.set_default_button(0)
  def done(d,res):
   try:
    if d.choose_finish(res)==1 and action:action()
   except GLib.Error:pass
  d.choose(self,None,done)
 def save_prefs(self):
  self.prefs.update({'theme':self.theme,'accent':self.accent,'start_dir':str(self.prefs.get('start_dir',HOME)),'show_hidden':self.show_hidden})
  try:
   CONFIG.parent.mkdir(parents=True,exist_ok=True)
   CONFIG.write_text(json.dumps(self.prefs,indent=2,ensure_ascii=False))
  except OSError as e:self.dialog('Préférences non enregistrées',str(e))
 def effective_dark(self):
  if self.theme=='dark':return True
  if self.theme=='light':return False
  settings=Gtk.Settings.get_default()
  return bool(settings.get_property('gtk-application-prefer-dark-theme')) if settings else False
 def restyle(self):
  dark=self.effective_dark()
  colors={'BG':'#111827' if dark else '#f5f8ff','SIDE':'#1b2940' if dark else '#e8effb',
          'FG':'#f4f7ff' if dark else '#17243a','BORDER':'#36455f' if dark else '#cbd8ed',
          'HOVER':'#304b72' if dark else '#d3e4ff','ACCENT':PALETTES[self.accent]}
  css=CSS_BASE
  for k,v in colors.items():css=css.replace(k,v)
  self.css.load_from_data(css.encode())
 def apply_theme(self):
  settings=Gtk.Settings.get_default()
  if settings and self.theme!='system':settings.set_property('gtk-application-prefer-dark-theme',self.theme=='dark')
  self.restyle()
 def update_theme_label(self):
  self.theme_button.set_label({'system':'🌓  Thème : système','dark':'🌙  Thème : sombre','light':'☀️  Thème : clair'}[self.theme])
 def toggle_theme(self,*_):
  self.theme={'system':'dark','dark':'light','light':'system'}[self.theme]
  self.apply_theme();self.update_theme_label();self.save_prefs()
 def settings_page(self,*_):
  self.clear();self.heading('⚙️ Paramètres')
  self.info('Personnalise ton application. Les changements sont enregistrés automatiquement.')
  self.info('Apparence')
  theme_row=Gtk.Box(spacing=8);self.content.append(theme_row)
  self.info('Choisis ton thème avec les boutons ci-dessous :')
  for label,val in [('☀️ Clair','light'),('🌙 Sombre','dark'),('🌓 Système','system')]:
   self.btn(theme_row,label,lambda _b,v=val:self.set_theme(v))
  self.info('Couleur principale')
  colors=Gtk.Box(spacing=8);self.content.append(colors)
  for label,val in [('💙 Bleu','blue'),('💜 Violet','purple'),('💚 Vert','green'),('🩵 Cyan','cyan')]:
   self.btn(colors,label,lambda _b,v=val:self.set_accent(v))
  self.info('Fichiers et sécurité')
  hidden=Gtk.CheckButton(label='Afficher les fichiers cachés')
  hidden.set_active(self.show_hidden)
  hidden.connect('toggled',lambda w:self.set_hidden_pref(w.get_active()))
  self.content.append(hidden)
  self.info('Dossier ouvert au démarrage (chemin complet)')
  start=Gtk.Entry(text=str(self.prefs.get('start_dir',HOME)));self.content.append(start)
  self.btn(self.content,'Enregistrer le dossier de démarrage',lambda *_:self.set_start_dir(start.get_text()))
  self.info('Les suppressions demandent toujours une confirmation. Cette protection ne peut pas être désactivée.')
  self.btn(self.content,'Réinitialiser les préférences',lambda *_:self.dialog('Réinitialiser les paramètres ?', 'Tes fichiers personnels ne seront pas touchés.',self.reset_prefs))
 def set_theme(self,value):
  self.theme=value;self.apply_theme();self.update_theme_label();self.save_prefs()
 def set_accent(self,value):
  self.accent=value;self.restyle();self.save_prefs()
 def set_hidden_pref(self,value):
  self.show_hidden=value;self.save_prefs()
 def set_start_dir(self,value):
  path=pathlib.Path(value).expanduser()
  if not path.is_dir():self.dialog('Dossier invalide','Choisis un dossier existant.');return
  self.prefs['start_dir']=str(path.resolve());self.save_prefs()
  self.dialog('Dossier enregistré','Ce dossier sera ouvert au prochain démarrage.')
 def reset_prefs(self):
  self.prefs={};self.theme='system';self.accent='blue';self.show_hidden=False
  self.prefs['start_dir']=str(HOME);self.apply_theme();self.update_theme_label();self.save_prefs();self.settings_page()
 def home(self,*_):
  self.clear();self.heading('🏠 Tableau de bord');self.info('Vos fichiers, applications et espace disque au même endroit. Aucune suppression automatique.')
  usage=shutil.disk_usage(HOME);used=usage.used/usage.total
  self.info(f'Disque principal : {usage.used/1e9:.1f} Go utilisés sur {usage.total/1e9:.1f} Go — {usage.free/1e9:.1f} Go libres')
  bar=Gtk.ProgressBar(fraction=used,show_text=True);bar.set_text(f'{used:.0%} utilisé');self.content.append(bar)
  for label,cb in [('📁 Explorer mes fichiers',self.files),('🎮 Voir mes jeux et applications',self.games),('🧹 Nettoyage sécurisé',self.clean)]:self.btn(self.content,label,cb).add_css_class('primary-action')
 def files(self,*_):
  self.clear();self.heading('📁 Explorateur de fichiers')
  toolbar=Gtk.Box(spacing=6);self.content.append(toolbar)
  self.btn(toolbar,'⬆ Parent',lambda *_:self.open_dir(self.cwd.parent))
  self.btn(toolbar,'🏠 Dossier personnel',lambda *_:self.open_dir(HOME))
  self.btn(toolbar,'📁 Nouveau dossier',self.mkdir)
  self.btn(toolbar,'👁 Fichiers cachés',self.hidden)
  self.path=Gtk.Entry(text=str(self.cwd));self.path.set_hexpand(True);self.path.connect('activate',lambda e:self.open_dir(pathlib.Path(e.get_text()).expanduser()));toolbar.append(self.path)
  self.search=Gtk.SearchEntry(placeholder_text='Filtrer ce dossier');self.search.connect('search-changed',lambda *_:self.refresh());self.content.append(self.search)
  scroll=Gtk.ScrolledWindow(vexpand=True);self.content.append(scroll)
  self.listbox=Gtk.ListBox();self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE);self.listbox.connect('row-activated',self.activate_row);scroll.set_child(self.listbox)
  actions=Gtk.Box(spacing=6);self.content.append(actions)
  for label,cb in [('Ouvrir',self.open_selected),('Copier vers…',lambda *_:self.choose_destination(False)),('Déplacer vers…',lambda *_:self.choose_destination(True)),('Renommer',self.rename),('Corbeille',self.trash),('Supprimer définitivement',self.delete)]:self.btn(actions,label,cb)
  actions.get_last_child().add_css_class('danger-action')
  self.info('Astuce : double-cliquez sur un dossier pour y entrer. La corbeille est privilégiée ; les suppressions demandent confirmation.')
  self.refresh()
 def open_dir(self,p):
  try:
   if not p.is_dir():raise NotADirectoryError(str(p))
   os.listdir(p);self.cwd=p;self.files()
  except Exception as e:self.dialog('Dossier inaccessible',str(e))
 def hidden(self,*_):self.show_hidden=not self.show_hidden;self.refresh()
 def refresh(self):
  if not hasattr(self,'listbox'):return
  while child:=self.listbox.get_first_child():self.listbox.remove(child)
  try:entries=sorted(self.cwd.iterdir(),key=lambda p:(not p.is_dir(),p.name.casefold()))
  except Exception as e:self.dialog('Lecture impossible',str(e));return
  q=self.search.get_text().casefold() if hasattr(self,'search') else ''
  self.entries=[p for p in entries if (self.show_hidden or not p.name.startswith('.')) and q in p.name.casefold()]
  for p in self.entries:
   row=Gtk.ListBoxRow();label=Gtk.Label(label=('📁  ' if p.is_dir() else '📄  ')+p.name,xalign=0,ellipsize=3);label.set_margin_top(7);label.set_margin_bottom(7);label.set_margin_start(8);row.set_child(label);row.path=p;self.listbox.append(row)
 def activate_row(self,_list,row):
  if row.path.is_dir():self.open_dir(row.path)
  else:
   try:Gio.AppInfo.launch_default_for_uri(row.path.as_uri(),None)
   except Exception as e:self.dialog('Ouverture impossible',str(e))
 def selected(self):
  row=self.listbox.get_selected_row();return row.path if row else None
 def open_selected(self,*_):
  row=self.listbox.get_selected_row()
  if row:self.activate_row(self.listbox,row)
 def mkdir(self,*_):self.prompt('Créer un dossier','Nom du dossier','Nouveau dossier',lambda name:self.perform(lambda:(self.cwd/name).mkdir(), 'Dossier créé'))
 def prompt(self,title,description,default,callback):
  d=Gtk.Dialog(title=title,transient_for=self,modal=True);d.add_button('Annuler',Gtk.ResponseType.CANCEL);d.add_button('Valider',Gtk.ResponseType.OK)
  entry=Gtk.Entry(text=default);entry.set_margin_top(15);entry.set_margin_bottom(15);entry.set_margin_start(15);entry.set_margin_end(15);d.get_content_area().append(Gtk.Label(label=description));d.get_content_area().append(entry)
  def response(d,r):
   value=entry.get_text().strip();d.destroy()
   if r==Gtk.ResponseType.OK:
    if not value or value in ('.','..') or '/' in value:self.dialog('Nom invalide','Utilisez un nom simple sans barre oblique.')
    else:callback(value)
  d.connect('response',response);d.present()
 def perform(self,func,success):
  try:func();self.refresh();self.dialog('Terminé',success)
  except Exception as e:self.dialog('Opération impossible',str(e))
 def rename(self,*_):
  p=self.selected()
  if p:self.prompt('Renommer','Nouveau nom',p.name,lambda name:self.perform(lambda:p.rename(p.with_name(name)) if not p.with_name(name).exists() else self.raise_exists(), 'Fichier renommé'))
 def raise_exists(self):raise FileExistsError('Un élément porte déjà ce nom.')
 def trash(self,*_):
  p=self.selected()
  if p:self.dialog('Mettre à la corbeille ?',str(p),lambda:self.perform(lambda:Gio.File.new_for_path(str(p)).trash(None),'Élément placé dans la corbeille'))
 def delete(self,*_):
  p=self.selected()
  if p:self.dialog('Suppression définitive',f'Cette action est irréversible :\n{p}',lambda:self.perform(lambda:shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink(),'Élément supprimé'))
 def choose_destination(self,move):
  p=self.selected()
  if not p:return
  dialog=Gtk.FileDialog(title='Choisir le dossier de destination')
  def chosen(d,res):
   try:
    dest=pathlib.Path(d.select_folder_finish(res).get_path())/p.name
    if dest.exists() or dest.is_symlink():self.dialog('Destination déjà occupée','Un élément de ce nom existe déjà. Aucun remplacement effectué.');return
    if p.is_dir() and not p.is_symlink() and (dest==p or p in dest.parents):self.dialog('Destination invalide','Impossible de placer un dossier dans lui-même.');return
    def op():
     if move:shutil.move(str(p),str(dest))
     elif p.is_dir():shutil.copytree(p,dest,symlinks=True)
     else:shutil.copy2(p,dest,follow_symlinks=False)
    self.dialog('Confirmer le déplacement' if move else 'Confirmer la copie',f'{p}\n→ {dest}',lambda:self.perform(op,'Opération terminée'))
   except GLib.Error:pass
  dialog.select_folder(self,None,chosen)
 def games(self,*_):
  self.clear();self.heading('🎮 Jeux et applications');self.info('Raccourcis vers les emplacements détectés. Les logiciels installés ne sont pas modifiés.')
  paths=[('Steam',HOME/'.local/share/Steam'),('Steam Flatpak',HOME/'.var/app/com.valvesoftware.Steam'),('Sober (Flatpak)',HOME/'.var/app/org.vinegarhq.Sober'),('Lunar Client',HOME/'.lunarclient'),('Applications utilisateur',HOME/'.local/share/applications'),('Applications système',pathlib.Path('/usr/share/applications')),('Applications Flatpak',HOME/'.var/app'),('Autres jeux',HOME/'Games')]
  for name,p in paths:
   if p.exists():self.btn(self.content,f'📂 {name} — {p}',lambda _b,p=p:self.open_dir(p))
  self.info('Flatpak installé : '+('oui' if shutil.which('flatpak') else 'non'))
  if shutil.which('flatpak'):
   try:
    result=subprocess.run(['flatpak','list','--app','--columns=name,application'],capture_output=True,text=True,timeout=8,check=False)
    self.info(result.stdout[:3500] or 'Aucune application Flatpak répertoriée.')
   except Exception as e:self.info(str(e))
 def clean(self,*_):
  self.clear();self.heading('🧹 Nettoyage sécurisé');self.info('Analyse indicative du cache utilisateur. Les documents, jeux et configurations ne sont jamais supprimés automatiquement.')
  cache=HOME/'.cache';total=0;count=0
  try:
   for root,dirs,files in os.walk(cache,followlinks=False):
    for f in files:
     try:total+=(pathlib.Path(root)/f).lstat().st_size;count+=1
     except OSError:pass
  except OSError:pass
  self.info(f'Cache utilisateur : environ {total/1e6:.1f} Mo, {count} fichiers. Certains caches sont utiles et seront recréés.')
  self.btn(self.content,'📂 Ouvrir le cache pour inspection',lambda *_:self.open_dir(cache))
  self.info('Pour vider la corbeille ou gérer les caches système, utilisez les outils Ubuntu dédiés. Aucune suppression massive intégrée.')
class App(Gtk.Application):
 def __init__(self):super().__init__(application_id='io.github.gestionstockage.Beta21',flags=Gio.ApplicationFlags.FLAGS_NONE)
 def do_activate(self):Window(self).present()
if __name__=='__main__':sys.exit(App().run(sys.argv))
