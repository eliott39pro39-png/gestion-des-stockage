#!/usr/bin/env python3
import os, sys, shutil, subprocess, pathlib, json, mimetypes, datetime, threading
from gi.repository import Gtk, Gio, GLib, Gdk
HOME=pathlib.Path.home()
APP='Gestion de stockage'
VERSION='26.9'
CONFIG=HOME/'.config/gestion-stockage-final/settings.json'
CSS_BASE = """
window, window.background { background-color: SOLIDBG; color: FG; }\n.app-root { background: BG; color: FG; }
.app-root { background-color: BG; }
.sidebar { background: SIDE; border-right: 1px solid BORDER; padding: 18px; min-width: 228px; }
.sidebar button { min-height: ROWHEIGHT; border-radius: 13px; margin: 3px 0; background: transparent; color: FG; border: 1px solid transparent; font-weight: 600; }
.sidebar button:hover { background: HOVER; border-color: BORDER; }
.brand { color: ACCENT; font-weight: 900; font-size: 18px; padding: 14px 5px 22px 5px; }
.content-area { background: transparent; color: FG; }
.main-panel { background: BG; }
.topbar { background: TOP; border-bottom: 1px solid BORDER; padding: 10px 20px; }
.topbar-title { font-size: 16px; font-weight: 800; color: FG; }
.heading { font-size: 26px; font-weight: 900; margin-bottom: 10px; color: FG; }
.primary-action { background: ACCENT; color: #071322; border-radius: 13px; font-weight: 800; min-height: 44px; }
.primary-action:hover { background: ACCENTHOVER; }
.danger-action { color: #ff788a; }
.version-badge { background: ACCENT; color: #071322; border-radius: 14px; padding: 6px 14px; font-weight: 900; }
list, listbox, scrolledwindow, viewport { background: transparent; color: FG; }
list row, listbox row { border-radius: 7px; margin: 1px 0; padding: 3px 8px; border-bottom: 1px solid BORDER; background: transparent; }
.file-name { font-weight: 650; font-size: 14px; color: FG; }
.file-meta { color: FG; opacity: .68; font-size: 11px; }
.file-symbol { color: ACCENT; font-size: 20px; min-width: 32px; }
.file-count { color: ACCENT; font-weight: 700; }
.file-toolbar { background: CARD; border: 1px solid BORDER; border-radius: 13px; padding: 8px; }

list row:selected, listbox row:selected { background: HOVER; border-left: 3px solid ACCENT; }\n.file-actions { background: CARD; border-radius: 12px; padding: 7px; }\n.file-filter { border-radius: 20px; padding: 3px 10px; }
progressbar trough { min-height: 16px; border-radius: 10px; background: BORDER; }
progressbar progress { background: ACCENT; border-radius: 10px; }
.card { background: CARD; border: 1px solid BORDER; border-radius: 20px; padding: 18px; }
button { border-radius: 11px; transition: background-color TRANSITION ease-in-out; }
button:hover { background-color: HOVER; }
button:active { opacity: .84; }
button:focus-visible { outline: 2px solid ACCENT; outline-offset: 2px; }
.sidebar button.active-nav { background: HOVER; border-left: 3px solid ACCENT; }
.mini-status { color: FG; opacity: .72; font-size: 12px; }

entry, searchentry { background: CARD; color: FG; border: 1px solid BORDER; border-radius: 12px; padding: 7px; }
separator { background: BORDER; }
"""
PALETTES = {
 'blue':'#287df0', 'purple':'#8059e8', 'green':'#168a70', 'cyan':'#078aaf', 'neon':'#00aaff'
}

class Window(Gtk.ApplicationWindow):
 def __init__(self,app):
  super().__init__(application=app,title=APP,default_width=1120,default_height=720)
  self.entries=[];self.file_sort='name';self.file_sort_reverse=False;self.file_filter='all'
  try: self.prefs=json.loads(CONFIG.read_text())
  except (OSError,ValueError,TypeError): self.prefs={}
  self.theme=self.prefs.get('theme','system')
  if self.theme not in ('system','dark','light'):self.theme='system'
  self.accent=self.prefs.get('accent','neon')
  if self.accent not in PALETTES:self.accent='blue'
  self.cwd=pathlib.Path(self.prefs.get('start_dir',str(HOME))).expanduser()
  if not self.cwd.is_dir():self.cwd=HOME
  self.show_hidden=bool(self.prefs.get('show_hidden',False))
  self.animations=bool(self.prefs.get('animations',True))
  self.file_view=self.prefs.get('file_view','list')
  self.background_style=self.prefs.get('background_style','aurora')
  if self.background_style not in ('aurora','solid','midnight'):self.background_style='aurora'
  self.density=self.prefs.get('density','comfortable')
  if self.density not in ('compact','comfortable','spacious'):self.density='comfortable'
  self.nav_style=self.prefs.get('nav_style','icons')
  if self.nav_style not in ('icons','text'):self.nav_style='icons'
  self.history=[];self.future=[];self._page_serial=0;self._active_page=None
  self.css=Gtk.CssProvider()
  self.restyle()
  Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),self.css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
  self.apply_theme()
  root=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL);root.add_css_class('app-root'); self.set_child(root)
  sidebar=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); sidebar.set_margin_top(20); sidebar.set_margin_start(12); sidebar.set_margin_end(12); sidebar.add_css_class('sidebar'); root.append(sidebar)
  title=Gtk.Label(label='◆  NEON STORAGE',xalign=0); title.add_css_class('brand'); sidebar.append(title)
  self.nav_buttons=[]
  for icon,name,callback in [('⌂','Accueil',self.home),('▣','Fichiers',self.files),('♻','Corbeille',self.trash_page),('◇','Jeux & applis',self.games),('✦','Nettoyage',self.clean),('◎','Fichiers inutiles',self.cleanup_page),('◷','Anciennes versions',self.versions_page),('⚙','Paramètres',self.settings_page)]:
   b=Gtk.Button();b.set_halign(Gtk.Align.FILL)
   b.connect('clicked',lambda _b,f=callback:f());sidebar.append(b)
   b.set_tooltip_text('Aller vers '+name);self.nav_buttons.append((b,icon,name))
  self.update_nav_labels()
  sidebar.append(Gtk.Separator())
  self.theme_button=Gtk.Button(); self.theme_button.connect('clicked',self.toggle_theme); sidebar.append(self.theme_button); self.update_theme_label()
  self.main_panel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);self.main_panel.set_hexpand(True);self.main_panel.add_css_class('main-panel');root.append(self.main_panel)
  topbar=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8);topbar.add_css_class('topbar');self.main_panel.append(topbar)
  toplabel=Gtk.Label(label='GESTION DE STOCKAGE   /   NEON EDITION',xalign=0,hexpand=True);toplabel.add_css_class('topbar-title');topbar.append(toplabel)
  self.btn(topbar,'□',self.toggle_maximize).set_tooltip_text('Agrandir ou restaurer la fenêtre')
  self.btn(topbar,'⛶',self.toggle_fullscreen).set_tooltip_text('Plein écran (F11)')
  version_badge=Gtk.Label(label='v'+VERSION);version_badge.add_css_class('version-badge');topbar.append(version_badge)
  self.content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); self.content.set_margin_top(18); self.content.set_margin_bottom(18); self.content.set_margin_start(20); self.content.set_margin_end(20); self.content.set_hexpand(True); self.content.add_css_class('content-area'); self.main_panel.append(self.content)
  key=Gtk.EventControllerKey();key.connect('key-pressed',self.on_key_pressed);self.add_controller(key)
  self.home()
 def on_key_pressed(self,_controller,keyval,_keycode,state):
  ctrl=bool(state & Gdk.ModifierType.CONTROL_MASK)
  alt=bool(state & Gdk.ModifierType.ALT_MASK)
  if keyval==Gdk.KEY_F11:self.toggle_fullscreen();return True
  if keyval==Gdk.KEY_Escape and self.is_fullscreen():self.unfullscreen();return True
  if ctrl and keyval in (Gdk.KEY_f,Gdk.KEY_F) and self._active_page=='Fichiers':self.search.grab_focus();return True
  if ctrl and keyval in (Gdk.KEY_r,Gdk.KEY_R) and self._active_page=='Fichiers':self.refresh();return True
  if ctrl and keyval in (Gdk.KEY_h,Gdk.KEY_H) and self._active_page=='Fichiers':self.hidden();return True
  if ctrl and keyval==Gdk.KEY_1:self.home();return True
  if alt and keyval==Gdk.KEY_Left and self._active_page=='Fichiers':self.go_back();return True
  if alt and keyval==Gdk.KEY_Right and self._active_page=='Fichiers':self.go_forward();return True
  return False
 def toggle_fullscreen(self,*_):
  if self.is_fullscreen():self.unfullscreen()
  else:self.fullscreen()
 def toggle_maximize(self,*_):
  if self.is_maximized():self.unmaximize()
  else:self.maximize()
 def clear(self):
  self._page_serial+=1
  self.content.set_opacity(0.0 if self.animations else 1.0)
  while child:=self.content.get_first_child():self.content.remove(child)
  serial=self._page_serial
  if self.animations:
   def fade_step(step=[0]):
    if serial!=self._page_serial:return False
    step[0]+=1
    self.content.set_opacity(min(1.0,step[0]/9))
    return step[0]<9
   GLib.timeout_add(18,fade_step)
  self._active_page=None
 def mark_page(self,name):
  self._active_page=name
  for button,_icon,label in self.nav_buttons:
   if label==name:button.add_css_class('active-nav')
   else:button.remove_css_class('active-nav')

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
  self.prefs.update({'theme':self.theme,'accent':self.accent,'start_dir':str(self.prefs.get('start_dir',HOME)),'show_hidden':self.show_hidden,'animations':self.animations,'file_view':self.file_view,'background_style':self.background_style,'density':self.density,'nav_style':self.nav_style})
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
  if dark:
   base='#0a1222';side='#0d1b30';top='#0d1b30';fg='#eaf4ff';border='#294365';hover='#19385b';card='#14253c'
  else:
   base='#edf5ff';side='#e1edff';top='#f6faff';fg='#10223e';border='#c2d5ed';hover='#c9e1ff';card='#ffffff'
  if self.background_style=='aurora':
   bg='linear-gradient(145deg, #0a1222, #122d51 58%, #123c56)' if dark else 'linear-gradient(145deg, #edf5ff, #d9edff 60%, #d8f7fa)'
  elif self.background_style=='midnight':
   bg='linear-gradient(145deg, #080b17, #151b39)' if dark else 'linear-gradient(145deg, #dce5f7, #c9d5ed)'
  else:bg=base
  accent=PALETTES[self.accent]
  colors={'BG':bg,'SOLIDBG':base,'SIDE':side,'TOP':top,'FG':fg,'BORDER':border,'HOVER':hover,'CARD':card,'ACCENT':accent,'ACCENTHOVER':'#55d5ff' if self.accent=='neon' else accent,'ROWHEIGHT':{'compact':'34px','comfortable':'43px','spacious':'54px'}[self.density],'TRANSITION':'170ms' if self.animations else '0ms'}
  css=CSS_BASE
  for k,v in sorted(colors.items(),key=lambda item:-len(item[0])):css=css.replace(k,v)
  self.css.load_from_data(css.encode())
 def update_nav_labels(self):
  for button,icon,name in self.nav_buttons:
   button.set_label((icon+'    ' if self.nav_style=='icons' else '')+name)
 def set_background_style(self,value):
  self.background_style=value;self.restyle();self.save_prefs()
 def set_density(self,value):
  self.density=value;self.restyle();self.save_prefs()
 def set_nav_style(self,value):
  self.nav_style=value;self.update_nav_labels();self.save_prefs()
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
  self.clear();self.mark_page('Paramètres');self.heading('PARAMÈTRES  ⚙')
  self.info('Personnalise ton application. Les changements sont enregistrés automatiquement.')
  self.info('NOUVEAU 26.4 — Réglages d’affichage')
  self.info('1. Fond de l’application')
  bgrow=Gtk.Box(spacing=8);self.content.append(bgrow)
  for label,val in [('✦ Aurore néon','aurora'),('Uni','solid'),('Nuit profonde','midnight')]:
   self.btn(bgrow,label,lambda _b,v=val:self.set_background_style(v))
  self.info('2. Espacement des éléments')
  densityrow=Gtk.Box(spacing=8);self.content.append(densityrow)
  for label,val in [('Compact','compact'),('Confort','comfortable'),('Aéré','spacious')]:
   self.btn(densityrow,label,lambda _b,v=val:self.set_density(v))
  self.info('3. Style du menu latéral')
  navrow=Gtk.Box(spacing=8);self.content.append(navrow)
  for label,val in [('Symboles + texte','icons'),('Texte seulement','text')]:
   self.btn(navrow,label,lambda _b,v=val:self.set_nav_style(v))
  self.info('Apparence')
  theme_row=Gtk.Box(spacing=8);self.content.append(theme_row)
  self.info('Choisis ton thème avec les boutons ci-dessous :')
  for label,val in [('☀️ Clair','light'),('🌙 Sombre','dark'),('🌓 Système','system')]:
   self.btn(theme_row,label,lambda _b,v=val:self.set_theme(v))
  self.info('Couleur principale — choix actuel : '+self.accent)
  colors=Gtk.Box(spacing=8);self.content.append(colors)
  for label,val in [('💙 Bleu','blue'),('💜 Violet','purple'),('💚 Vert','green'),('🩵 Cyan','cyan'),('⚡ Néon','neon')]:
   self.btn(colors,label,lambda _b,v=val:self.set_accent(v))
  self.info('Effets visuels et explorateur — transition douce entre les pages (désactivable)')
  anim=Gtk.CheckButton(label='Animations et transitions');anim.set_active(self.animations);anim.connect('toggled',lambda w:self.set_animations(w.get_active()));self.content.append(anim)
  self.btn(self.content,'Changer la vue des fichiers (liste / grandes icônes)',self.toggle_view)
  self.info('Fichiers et sécurité')
  hidden=Gtk.CheckButton(label='Afficher les fichiers cachés')
  hidden.set_active(self.show_hidden)
  hidden.connect('toggled',lambda w:self.set_hidden_pref(w.get_active()))
  self.content.append(hidden)
  self.info('Dossier ouvert au démarrage (chemin complet)')
  start=Gtk.Entry(text=str(self.prefs.get('start_dir',HOME)));self.content.append(start)
  self.btn(self.content,'Enregistrer le dossier de démarrage',lambda *_:self.set_start_dir(start.get_text()))
  self.info('Les suppressions demandent toujours une confirmation. Cette protection ne peut pas être désactivée.')
  self.btn(self.content,'📋 À propos et nouveautés',self.about_page)
  self.btn(self.content,'Réinitialiser les préférences',lambda *_:self.dialog('Réinitialiser les paramètres ?', 'Tes fichiers personnels ne seront pas touchés.',self.reset_prefs))
 def versions_page(self,*_):
  self.clear();self.mark_page('Anciennes versions');self.heading('ANCIENNES VERSIONS  ◷')
  self.info('Les anciennes versions sont des éditions de test. Les graphiques ont été retirés des copies fournies dans cette archive.')
  archive=pathlib.Path(__file__).resolve().parent/'versions'
  self.heading('VERSIONS BÊTA')
  for version in ('26.9','26.7','26.6','26.5.1','26.5','26.4','26.3','26.2','2.1','2.0','1.0'):
   script=archive/version/'app.py'
   if script.is_file():
    row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10);self.content.append(row)
    row.append(Gtk.Label(label='Version '+version,hexpand=True,xalign=0))
    self.btn(row,'Ouvrir ↗',lambda _b,p=script,v=version:self.launch_beta(p,v))
  self.heading('VERSIONS BUGGUÉES  ⚠')
  self.info('Ces éditions ont rencontré des problèmes de graphiques ou de fenêtre. Ne les utilise pas pour des fichiers importants.')
  for version in ('26.8','26.8.2','26.8.3','26.8.4','26.8.5','26.8.6'):
   script=archive/version/'app.py'
   if script.is_file():
    row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10);self.content.append(row)
    row.append(Gtk.Label(label='Version '+version+' — bugguée',hexpand=True,xalign=0))
    self.btn(row,'Ouvrir ⚠',lambda _b,p=script,v=version:self.dialog('Version bugguée','Cette version a eu des problèmes connus. Les graphiques ont été retirés de cette copie. Ouvrir quand même ?',lambda:self.launch_beta(p,v)))
 def launch_beta(self,script,version):
  try:
   subprocess.Popen([sys.executable,str(script)],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   self.notify('Version bêta lancée','Gestion de stockage '+version)
  except OSError as exc:self.dialog('Impossible de lancer la version',str(exc))
 def about_page(self,*_):
  self.clear();self.heading('GESTION DE STOCKAGE — '+VERSION)
  self.info('27.0 — Navigation fluide : fondu doux, survol et sélection des menus, raccourcis clavier, boutons de fenêtre.')
  self.info('26.9 — Retour à la base 26.7. Graphiques supprimés. Archives séparées en bêta et versions bugguées.')
  self.info('Nouveautés 26.7 — Explorateur apaisé')
  self.info('• Lignes sobres, mode de lecture au choix, filtres rapides et actions contextuelles.')
  self.info('• Lignes de fichiers aérées, noms et informations séparés.')
  self.info('• Tri par nom, taille ou date, avec inversion du sens.')
  self.info('• Compteur des résultats pendant la recherche.')
  self.info('• Icônes différentes pour les dossiers, images et autres fichiers.')
  self.info('• Version 26.5.1 ajoutée aux archives bêta.')
  self.info('Nouveautés 26.5.1 — Nettoyage prévisualisé et correctif des couleurs')
  self.info('• Nouvel onglet Fichiers inutiles : aperçu des caches sélectionnés et mise à la corbeille après confirmation.')
  self.info('• Correction du remplacement des couleurs CSS et indicateur de couleur active.')
  self.info('• Correction du script install.sh de la 26.5.')
  self.info('• Nouvelle page Anciennes versions : lancement séparé des versions 1.0 à 26.4.')
  self.info('• Paramètres isolés par version pour éviter les conflits.')
  self.info('• Version actuelle 26.5 conservée pendant les tests.')
  for item in ['Interface et navigation entièrement redessinées avec symboles cohérents.', 'Fond opaque avec trois ambiances : Aurore néon, Uni, Nuit profonde.', 'Paramètres : densité de l’interface et style du menu latéral.', 'Graphiques des principaux dossiers avec analyse en arrière-plan.', 'Explorateur : précédent/suivant, favoris, vue à grandes icônes, taille des fichiers.', 'Corbeille : liste des éléments et restauration avec contrôle des conflits.', 'Notifications locales après les opérations et avertissement si le disque est presque plein.', 'Personnalisation : couleur bleu néon, transitions et vue enregistrées.', 'Toutes les fonctions de la 26.2 conservées.']:
   self.info('• '+item)
  self.info('Les mises à jour futures pourront ajouter, modifier ou retirer des fonctions selon tes demandes.')
  self.btn(self.content,'← Retour aux paramètres',self.settings_page)
 def set_animations(self,value):
  self.animations=value;self.save_prefs();self.restyle()
 def toggle_view(self,*_):
  self.file_view='icons' if self.file_view=='list' else 'list';self.save_prefs();self.files()
 def notify(self,title,message):
  try:
   n=Gio.Notification.new(title);n.set_body(message);self.get_application().send_notification(None,n)
  except Exception:pass
 def set_theme(self,value):
  self.theme=value;self.apply_theme();self.update_theme_label();self.save_prefs()
 def set_accent(self,value):
  self.accent=value;self.restyle();self.save_prefs();self.settings_page()
 def set_hidden_pref(self,value):
  self.show_hidden=value;self.save_prefs()
 def set_start_dir(self,value):
  path=pathlib.Path(value).expanduser()
  if not path.is_dir():self.dialog('Dossier invalide','Choisis un dossier existant.');return
  self.prefs['start_dir']=str(path.resolve());self.save_prefs()
  self.dialog('Dossier enregistré','Ce dossier sera ouvert au prochain démarrage.')
 def reset_prefs(self):
  self.prefs={};self.theme='system';self.accent='neon';self.show_hidden=False;self.background_style='aurora';self.density='comfortable';self.nav_style='icons';self.update_nav_labels()
  self.prefs['start_dir']=str(HOME);self.apply_theme();self.update_theme_label();self.save_prefs();self.settings_page()
 def home(self,*_):
  self.clear();self.mark_page('Accueil');self.heading('TABLEAU DE BORD  ✦');self.info('Vos fichiers, applications et espace disque au même endroit. Aucune suppression automatique.')
  usage=shutil.disk_usage(HOME);used=usage.used/usage.total
  self.info(f'Disque principal : {usage.used/1e9:.1f} Go utilisés sur {usage.total/1e9:.1f} Go — {usage.free/1e9:.1f} Go libres')
  bar=Gtk.ProgressBar(fraction=used,show_text=True);bar.set_text(f'{used:.0%} utilisé');self.content.append(bar)
  if usage.free/usage.total<0.10:self.info('⚠️ Espace disque faible : moins de 10 % disponibles.')
  for label,cb in [('📁 Explorer mes fichiers',self.files),('🎮 Voir mes jeux et applications',self.games),('🧹 Nettoyage sécurisé',self.clean)]:self.btn(self.content,label,cb).add_css_class('primary-action')
 def files(self,*_):
  self.clear();self.mark_page('Fichiers');self.heading('EXPLORATEUR  ▣')
  toolbar=Gtk.Box(spacing=6);toolbar.add_css_class('file-toolbar');self.content.append(toolbar)
  self.btn(toolbar,'← Retour',self.go_back)
  self.btn(toolbar,'→ Suivant',self.go_forward)
  self.btn(toolbar,'⭐ Favori',self.add_favorite)
  self.btn(toolbar,'⬆ Parent',lambda *_:self.open_dir(self.cwd.parent))
  self.btn(toolbar,'🏠 Dossier personnel',lambda *_:self.open_dir(HOME))
  self.btn(toolbar,'📁 Nouveau dossier',self.mkdir)
  self.btn(toolbar,'👁 Fichiers cachés',self.hidden)
  self.path=Gtk.Entry(text=str(self.cwd));self.path.set_hexpand(True);self.path.connect('activate',lambda e:self.open_dir(pathlib.Path(e.get_text()).expanduser()));toolbar.append(self.path)
  fav=Gtk.Box(spacing=5);self.content.append(fav)
  for name,path in [('🏠',HOME),('📥',HOME/'Téléchargements'),('🖼️',HOME/'Images')]:
   if path.is_dir():self.btn(fav,name,lambda _b,p=path:self.open_dir(p))
  for path in self.prefs.get('favorites',[])[:5]:
   pp=pathlib.Path(path)
   if pp.is_dir():self.btn(fav,'⭐ '+pp.name,lambda _b,p=pp:self.open_dir(p))
  findrow=Gtk.Box(spacing=10);self.content.append(findrow)
  self.search=Gtk.SearchEntry(placeholder_text='Rechercher un fichier ou un dossier ici…');self.search.set_hexpand(True);self.search.connect('search-changed',lambda *_:self.refresh());findrow.append(self.search)
  self.btn(findrow,'Nom ↕',lambda *_:self.change_file_sort('name'))
  self.btn(findrow,'Taille ↕',lambda *_:self.change_file_sort('size'))
  self.btn(findrow,'Date ↕',lambda *_:self.change_file_sort('date'))
  self.btn(findrow,'▦ / ☷',self.toggle_file_view)
  filters=Gtk.Box(spacing=5);self.content.append(filters)
  for label,key in [('Tous','all'),('Dossiers','folders'),('Images','images'),('Documents','documents')]:
   self.btn(filters,label,lambda _b,k=key:self.set_file_filter(k)).add_css_class('file-filter')
  self.count_label=Gtk.Label(xalign=0);self.count_label.add_css_class('file-count');self.content.append(self.count_label)
  scroll=Gtk.ScrolledWindow(vexpand=True);self.content.append(scroll)
  self.listbox=Gtk.ListBox();self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE);self.listbox.connect('row-activated',self.activate_row);self.listbox.connect('row-selected',lambda *_:self.update_file_actions());scroll.set_child(self.listbox)
  actions=Gtk.Box(spacing=6);actions.add_css_class('file-actions');self.content.append(actions);self.file_actions=actions
  for label,cb in [('Ouvrir',self.open_selected),('Copier vers…',lambda *_:self.choose_destination(False)),('Déplacer vers…',lambda *_:self.choose_destination(True)),('Renommer',self.rename),('Corbeille',self.trash),('Supprimer définitivement',self.delete)]:self.btn(actions,label,cb)
  actions.get_last_child().add_css_class('danger-action');actions.set_visible(False)
  self.info('Sélectionne un élément pour afficher les actions. Double-clique pour ouvrir.  •  Ctrl+F rechercher  •  Alt+← retour  •  Ctrl+R actualiser')
  self.refresh()
 def toggle_file_view(self,*_):
  self.file_view='grid' if self.file_view=='list' else 'list';self.save_prefs();self.refresh()
 def set_file_filter(self,key):
  self.file_filter=key;self.refresh()
 def update_file_actions(self):
  if hasattr(self,'file_actions'):self.file_actions.set_visible(bool(self.listbox.get_selected_row()))
 def open_dir(self,p):
  try:
   if not p.is_dir():raise NotADirectoryError(str(p))
   os.listdir(p)
   if p!=self.cwd:self.history.append(self.cwd);self.future.clear()
   self.cwd=p;self.files()
  except Exception as e:self.dialog('Dossier inaccessible',str(e))
 def go_back(self,*_):
  if self.history:
   p=self.history.pop();self.future.append(self.cwd);self.cwd=p;self.files()
 def go_forward(self,*_):
  if self.future:
   p=self.future.pop();self.history.append(self.cwd);self.cwd=p;self.files()
 def add_favorite(self,*_):
  fav=self.prefs.setdefault('favorites',[])
  if str(self.cwd) not in fav:fav.append(str(self.cwd));self.save_prefs()
  self.files()
 def hidden(self,*_):self.show_hidden=not self.show_hidden;self.save_prefs();self.refresh()
 def change_file_sort(self,mode):
  if self.file_sort==mode:self.file_sort_reverse=not self.file_sort_reverse
  else:self.file_sort=mode;self.file_sort_reverse=False
  self.refresh()
 def refresh(self):
  if not hasattr(self,'listbox'):return
  while child:=self.listbox.get_first_child():self.listbox.remove(child)
  try:entries=list(self.cwd.iterdir())
  except Exception as e:self.dialog('Lecture impossible',str(e));return
  q=self.search.get_text().casefold() if hasattr(self,'search') else ''
  self.entries=[p for p in entries if (self.show_hidden or not p.name.startswith('.')) and q in p.name.casefold()]
  image_ext={'.png','.jpg','.jpeg','.webp','.gif','.bmp','.svg'}
  doc_ext={'.pdf','.txt','.doc','.docx','.odt','.md','.csv','.xls','.xlsx','.ods'}
  if self.file_filter=='folders':self.entries=[p for p in self.entries if p.is_dir()]
  elif self.file_filter=='images':self.entries=[p for p in self.entries if p.is_file() and p.suffix.lower() in image_ext]
  elif self.file_filter=='documents':self.entries=[p for p in self.entries if p.is_file() and p.suffix.lower() in doc_ext]
  def order(p):
   try:
    if self.file_sort=='size':return p.stat().st_size if p.is_file() else 0
    if self.file_sort=='date':return p.stat().st_mtime
   except OSError:return 0
   return p.name.casefold()
  self.entries.sort(key=order,reverse=self.file_sort_reverse)
  self.entries.sort(key=lambda p:not p.is_dir())
  self.count_label.set_text(f'{len(self.entries)} élément(s)  ·  '+{'all':'Tous','folders':'Dossiers','images':'Images','documents':'Documents'}[self.file_filter]+'  ·  Tri : '+{'name':'nom','size':'taille','date':'date'}[self.file_sort])
  for p in self.entries:
   row=Gtk.ListBoxRow();line=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=12)
   compact=self.file_view=='list'
   line.set_margin_top(4 if compact else 11);line.set_margin_bottom(4 if compact else 11);line.set_margin_start(8);line.set_margin_end(8)
   is_dir=p.is_dir()
   icon=Gtk.Label(label='▣' if is_dir else ('◈' if p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.gif') else '▤'),xalign=.5)
   icon.add_css_class('file-symbol');line.append(icon)
   labels=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=2);labels.set_hexpand(True);line.append(labels)
   name=Gtk.Label(label=p.name,xalign=0,ellipsize=3);name.set_max_width_chars(75);name.add_css_class('file-name');labels.append(name)
   try:
    st=p.stat();date=datetime.datetime.fromtimestamp(st.st_mtime).strftime('%d/%m/%Y')
    size=('Dossier' if is_dir else (f'{st.st_size/1024/1024:.1f} Mo' if st.st_size>=1024*1024 else f'{st.st_size/1024:.0f} Ko'))
    meta=f'{size}  •  Modifié le {date}'
   except OSError:meta='Informations indisponibles'
   details=Gtk.Label(label=meta,xalign=0);details.add_css_class('file-meta');labels.append(details)
   if not compact:line.set_margin_start(24);line.set_margin_end(24)
   row.set_child(line);row.path=p;self.listbox.append(row)
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
  try:func();self.refresh();self.notify('Gestion de stockage',success);self.dialog('Terminé',success)
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
 def trash_page(self,*_):
  self.clear();self.mark_page('Corbeille');self.heading('🗑️ Corbeille intelligente')
  self.info('Restaurer un élément à son emplacement d’origine. Aucune suppression définitive depuis cette page.')
  info_dir=HOME/'.local/share/Trash/info';files_dir=HOME/'.local/share/Trash/files'
  if not info_dir.is_dir():self.info('La corbeille est vide ou indisponible.');return
  import configparser,urllib.parse
  items=sorted(info_dir.glob('*.trashinfo'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]
  if not items:self.info('Aucun élément dans la corbeille utilisateur.');return
  scroll=Gtk.ScrolledWindow(vexpand=True);self.content.append(scroll)
  box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6);scroll.set_child(box)
  for meta in items:
   cfg=configparser.ConfigParser(interpolation=None)
   try:
    cfg.read(meta,encoding='utf-8');raw=cfg['Trash Info']['Path']
    original=pathlib.Path(urllib.parse.unquote(raw))
    if not original.is_absolute():continue
    trashed=files_dir/meta.name.removesuffix('.trashinfo')
    if not trashed.exists() and not trashed.is_symlink():continue
   except (OSError,KeyError,ValueError):continue
   line=Gtk.Box(spacing=8);line.add_css_class('card');box.append(line)
   label=Gtk.Label(label=f'{trashed.name} → {original}',xalign=0,hexpand=True,wrap=True);line.append(label)
   self.btn(line,'Restaurer',lambda _b,t=trashed,m=meta,o=original:self.restore_item(t,m,o))
 def restore_item(self,trashed,meta,original):
  def action():
   if original.exists() or original.is_symlink():self.dialog('Conflit','Un fichier existe déjà à cet emplacement. Rien n’a été remplacé.');return
   if not original.parent.is_dir():self.dialog('Dossier absent','Le dossier d’origine n’existe plus. Aucun déplacement effectué.');return
   try:shutil.move(str(trashed),str(original));meta.unlink();self.notify('Corbeille','Fichier restauré');self.trash_page()
   except Exception as e:self.dialog('Restauration impossible',str(e))
  self.dialog('Restaurer cet élément ?',f'{trashed.name} → {original}',action)
 def games(self,*_):
  self.clear();self.mark_page('Jeux & applis');self.heading('JEUX & APPLICATIONS  ◇');self.info('Raccourcis vers les emplacements détectés. Les logiciels installés ne sont pas modifiés.')
  paths=[('Steam',HOME/'.local/share/Steam'),('Steam Flatpak',HOME/'.var/app/com.valvesoftware.Steam'),('Sober (Flatpak)',HOME/'.var/app/org.vinegarhq.Sober'),('Lunar Client',HOME/'.lunarclient'),('Applications utilisateur',HOME/'.local/share/applications'),('Applications système',pathlib.Path('/usr/share/applications')),('Applications Flatpak',HOME/'.var/app'),('Autres jeux',HOME/'Games')]
  for name,p in paths:
   if p.exists():self.btn(self.content,f'📂 {name} — {p}',lambda _b,p=p:self.open_dir(p))
  self.info('Flatpak installé : '+('oui' if shutil.which('flatpak') else 'non'))
  if shutil.which('flatpak'):
   try:
    result=subprocess.run(['flatpak','list','--app','--columns=name,application'],capture_output=True,text=True,timeout=8,check=False)
    self.info(result.stdout[:3500] or 'Aucune application Flatpak répertoriée.')
   except Exception as e:self.info(str(e))
 def cleanup_page(self,*_):
  self.clear();self.mark_page('Fichiers inutiles');self.heading('FICHIERS INUTILES  ◎')
  self.info('Aucun fichier supprimé automatiquement. Seuls les caches de miniatures et de téléchargements pip sont proposés, jamais tes documents, jeux ou mondes.')
  candidates=[('Miniatures Ubuntu',HOME/'.cache/thumbnails'),('Cache de téléchargements Python pip',HOME/'.cache/pip')]
  for title,path in candidates:
   if not path.is_dir() or path.is_symlink():continue
   count=0;size=0;sample=[]
   try:
    for folder,dirs,files in os.walk(path,followlinks=False):
     dirs[:]=[d for d in dirs if not (pathlib.Path(folder)/d).is_symlink()]
     for name in files:
      f=pathlib.Path(folder)/name
      try:
       size+=f.lstat().st_size;count+=1
       if len(sample)<5:sample.append(str(f.relative_to(path)))
      except OSError:pass
   except OSError:continue
   row=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5);row.add_css_class('card');self.content.append(row)
   row.append(Gtk.Label(label=f'{title} — {count} fichiers, environ {size/1e6:.1f} Mo',xalign=0))
   row.append(Gtk.Label(label='Dossier : '+str(path),xalign=0,wrap=True))
   for name in sample:row.append(Gtk.Label(label='• '+name,xalign=0,wrap=True))
   self.btn(row,'Voir le dossier',lambda _b,p=path:self.open_dir(p))
   self.btn(row,'Mettre ce cache à la corbeille…',lambda _b,p=path,t=title:self.confirm_cache_trash(p,t)).add_css_class('danger-action')
  self.info('La corbeille permet de récupérer les éléments. Certaines applications recréeront leurs caches. Les tailles sont indicatives.')
 def confirm_cache_trash(self,path,title):
  allowed=[HOME/'.cache/thumbnails',HOME/'.cache/pip']
  if path not in allowed or not path.is_dir() or path.is_symlink():return
  def action():
   try:
    Gio.File.new_for_path(str(path)).trash(None)
    self.notify('Cache déplacé à la corbeille',title)
    self.cleanup_page()
   except Exception as exc:self.dialog('Déplacement impossible',str(exc))
  self.dialog('Déplacer ce dossier à la corbeille ?',f'{title}\\n{path}\\n\\nLes fichiers affichés seront déplacés dans la corbeille. Aucune suppression définitive.',action)
 def clean(self,*_):
  self.clear();self.mark_page('Nettoyage');self.heading('NETTOYAGE SÉCURISÉ  ✦');self.info('Analyse indicative du cache utilisateur. Les documents, jeux et configurations ne sont jamais supprimés automatiquement.')
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
 def __init__(self):super().__init__(application_id='io.github.gestionstockage.Beta269',flags=Gio.ApplicationFlags.FLAGS_NONE)
 def do_activate(self):Window(self).present()
if __name__=='__main__':sys.exit(App().run(sys.argv))
