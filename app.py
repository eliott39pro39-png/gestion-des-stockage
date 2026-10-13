#!/usr/bin/env python3
import os, sys, shutil, subprocess, pathlib, json, mimetypes, datetime, threading, urllib.parse, urllib.request, re, shlex, hashlib
from gi.repository import Gtk, Gio, GLib, Gdk
import assistant_tools
import assistant_history
import smart_organizer
HOME=pathlib.Path.home()
APP='Gestion de stockage'
VERSION='27.7.0'
CONFIG=HOME/'.config/gestion-stockage-final/settings.json'
CSS_BASE = """
window, window.background { background-color: SOLIDBG; color: FG; }\n.app-root { background: BG; color: FG; }
.app-root { background-color: BG; }
.sidebar { background: SIDE; border-right: 1px solid BORDER; padding: 12px; min-width: 155px; }
.sidebar button { min-height: ROWHEIGHT; border-radius: 13px; margin: 3px 0; background: transparent; color: FG; border: 1px solid transparent; font-weight: 600; }
.sidebar button:hover { background: HOVER; border-color: BORDER; }
.brand { color: ACCENT; font-weight: 800; font-size: 17px; padding: 12px 5px 16px 5px; }
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
.hero { border-radius: 19px; border: 1px solid BORDER; }
.section-banner { border-radius: 17px; border: 1px solid BORDER; background: CARD; }
.section-banner-title { color: #ffffff; font-weight: 900; font-size: 24px; text-shadow: 0px 2px 6px #08101c; }
.release-card:hover, .dashboard-card:hover { border-color: ACCENT; }

.hero-title { font-size: 30px; font-weight: 900; color: #ffffff; text-shadow: 0px 2px 8px #08101c; }
.hero-subtitle { font-size: 14px; color: #edf4ff; text-shadow: 0px 1px 5px #08101c; }
.hero-version { font-size: 11px; font-weight: 800; color: #a9d8ff; }
.dashboard-card { background: CARD; border: 1px solid BORDER; border-radius: 18px; padding: 18px; }
.dashboard-value { font-size: 24px; font-weight: 900; color: FG; }
.dashboard-label { font-size: 12px; color: FG; opacity: .75; }
.dashboard-section { font-size: 17px; font-weight: 800; color: FG; }
button { border-radius: 11px;  }
button:hover { background-color: HOVER; }
button:active { opacity: .84; }
button:focus-visible { outline: 2px solid ACCENT; outline-offset: 2px; }
.sidebar button.active-nav { background: HOVER; border-left: 3px solid ACCENT; }
.mini-status { color: FG; opacity: .72; font-size: 12px; }

entry, searchentry { background: CARD; color: FG; border: 1px solid BORDER; border-radius: 12px; padding: 7px; }
.release-card { background: CARD; border: 1px solid BORDER; border-radius: 15px; padding: 12px; margin: 3px 0; }
.release-title { font-size: 16px; font-weight: 800; color: ACCENT; }
button {  }
separator { background: BORDER; }
"""
PALETTES = {
 'blue':'#287df0', 'purple':'#8059e8', 'green':'#168a70', 'cyan':'#078aaf', 'neon':'#00aaff'
}

RELEASES = [('27.4.0', ['Recherche des mises à jour officielles sur GitHub', 'Téléchargement et installation guidée', 'Transitions fondues entre pages GTK4']), ('27.3.0', ['Transitions légères entre les pages']), ('27.2', ['Page Favoris dédiée', 'Copie du chemin du dossier courant', 'Accès au dossier parent', 'Raccourci F5 pour actualiser', 'Ctrl+4 pour les Favoris', 'Ctrl+5 pour les Paramètres', 'Ctrl+6 pour les Raccourcis']), ('27.1', ['Copier le chemin complet du fichier sélectionné', 'Retirer un dossier des favoris', 'Nouvel onglet Raccourcis clavier']), ('27.0.3', ['Fenêtre adaptative avec défilement de secours', 'Bannières panoramiques sur les autres pages', 'Boutons et réglages réorganisés']), ('27.0.2', ['Fond panoramique montagneux sur l’accueil', 'Barres d’outils adaptatives et correction de largeur minimale', 'Nouvelle présentation inspirée de la maquette']), ('27.0.1', ['Interface inspirée du tableau de bord néon', 'Correction du défilement et des contraintes de largeur', 'Accueil avec cartes de stockage et accès rapides']), ('27.0', ['Nouvel onglet Téléchargements et historique détaillé des mises à jour', 'Nouvelle identité visuelle et icône', 'Navigation fluide, accès rapides et raccourcis supplémentaires']), ('26.9', ['Retour à la base stable 26.7 sans graphiques', 'Versions bêta et bugguées séparées', 'Fluid Edition : transitions légères et personnalisation']), ('26.8.6', ['Tentative de calcul progressif des graphiques — édition bugguée']), ('26.8.5', ['Catégorie Versions bugguées et avertissement avant lancement']), ('26.8.4', ['Correctifs d’affichage et export CSV — édition bugguée']), ('26.8.3', ['Graphiques circulaires et barres — édition bugguée']), ('26.8.2', ['Correctifs de fenêtre et ouverture de dossiers — édition bugguée']), ('26.8', ['Graphiques de stockage redessinés — édition bugguée']), ('26.7', ['Explorateur simplifié, filtres, actions contextuelles']), ('26.6', ['Tri des fichiers, compteur et icônes']), ('26.5.1', ['Nettoyage prévisualisé et corrections de couleurs']), ('26.5', ['Archives des anciennes versions et améliorations']), ('26.4', ['Thèmes, densité et styles du menu']), ('26.3', ['Personnalisation et interface améliorée']), ('26.2', ['Gestion du stockage et de la navigation']), ('2.1', ['Améliorations de l’explorateur']), ('2.0', ['Nouvelle interface']), ('1.0', ['Première édition'])]

class Window(Gtk.ApplicationWindow):
 def __init__(self,app):
  super().__init__(application=app,title=APP,default_width=1024,default_height=720)
  self.entries=[];self.file_sort='name';self.file_sort_reverse=False;self.file_filter='all'
  try: self.prefs=json.loads(CONFIG.read_text())
  except (OSError,ValueError,TypeError): self.prefs={}
  self.language=self.prefs.get('language')
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
  self.history=[];self.future=[];self._page_serial=0;self._active_page=None;self._page_animation_id=None;self._update_busy=False;self._update_release=None
  self.css=Gtk.CssProvider()
  self.restyle()
  Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),self.css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
  self.apply_theme()
  root=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL);root.add_css_class('app-root'); self.set_child(root)
  sidebar=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);sidebar.set_size_request(155,-1); sidebar.set_margin_top(20); sidebar.set_margin_start(12); sidebar.set_margin_end(12); sidebar.add_css_class('sidebar'); side_scroll=Gtk.ScrolledWindow();side_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);side_scroll.set_min_content_width(178);side_scroll.set_kinetic_scrolling(True);side_scroll.set_child(sidebar);root.append(side_scroll)
  title=Gtk.Label(label='▣  NEON STORAGE',xalign=0); title.add_css_class('brand'); sidebar.append(title)
  self.nav_buttons=[]
  for icon,name,callback in [('⌂','Accueil',self.home),('🤖','Assistant',self.assistant_page),('▣','Fichiers',self.files),('♻','Corbeille',self.trash_page),('◇','Jeux & applis',self.games),('✦','Nettoyage',self.clean),('◈','Détective stockage',self.storage_detective),('◎','Radar doublons',self.duplicates_page),('◎','Fichiers inutiles',self.cleanup_page),('⬇','Téléchargements',self.downloads_page),('★','Favoris',self.favorites_page),('◷','Anciennes versions',self.versions_page),('⬆','Mises à jour',self.updates_page),('⚙','Paramètres',self.settings_page),('⌨','Raccourcis',self.shortcuts_page)]:
   b=Gtk.Button();b.set_halign(Gtk.Align.FILL)
   b.connect('clicked',lambda _b,f=callback:f());sidebar.append(b)
   b.set_tooltip_text('Aller vers '+name);self.nav_buttons.append((b,icon,name))
  self.update_nav_labels()
  sidebar.append(Gtk.Separator())
  self.theme_button=Gtk.Button(); self.theme_button.connect('clicked',self.toggle_theme); sidebar.append(self.theme_button); self.update_theme_label()
  self.main_panel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);self.main_panel.set_hexpand(True);self.main_panel.add_css_class('main-panel');root.append(self.main_panel)
  topbar=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8);topbar.add_css_class('topbar');self.main_panel.append(topbar)
  toplabel=Gtk.Label(label='GESTION DE STOCKAGE',xalign=0,hexpand=True,ellipsize=3);toplabel.add_css_class('topbar-title');topbar.append(toplabel)
  self.btn(topbar,'□',self.toggle_maximize).set_tooltip_text('Agrandir ou restaurer la fenêtre')
  self.btn(topbar,'⛶',self.toggle_fullscreen).set_tooltip_text('Plein écran (F11)')
  version_badge=Gtk.Label(label='v'+VERSION);version_badge.add_css_class('version-badge');topbar.append(version_badge)
  self.page_stack=Gtk.Stack(vexpand=True,hexpand=True);self.page_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE);self.page_stack.set_transition_duration(360);self.main_panel.append(self.page_stack)
  self.content=None;self.page_scroll=None
  key=Gtk.EventControllerKey();key.connect('key-pressed',self.on_key_pressed);self.add_controller(key)
  if self.language in ('fr','en'):
   self.home()
   GLib.idle_add(self.show_release_notes)
  else:self.language_setup()
 def tr(self,fr,en):
  return en if self.language=='en' else fr
 def language_setup(self):
  self.clear();self.mark_page('Langue')
  self.info('Choisissez votre langue / Choose your language')
  self.info('Le français et l’anglais sont disponibles. / French and English are available.')
  self.btn(self.content,'Français',lambda *_:self.set_language('fr'))
  self.btn(self.content,'English',lambda *_:self.set_language('en'))
 def set_language(self,language):
  if language not in ('fr','en'):return
  self.language=language;self.prefs['language']=language
  self.save_prefs();self.update_nav_labels();self.home()
  GLib.idle_add(self.show_release_notes)
 def show_release_notes(self):
  if self.prefs.get('last_seen_version')==VERSION:return False
  notes={'27.7.0':('Explorateur simplifié, recherche améliorée, suivi des recherches et choix de langue.',
                   'Simpler file explorer, improved search, search progress and language selection.')}
  fr,en=notes.get(VERSION,('Améliorations et corrections.','Improvements and fixes.'))
  message=self.tr(fr,en)
  def acknowledged():
   self.prefs['last_seen_version']=VERSION
   self.save_prefs()
  d=Gtk.AlertDialog()
  d.set_message(self.tr('Nouveautés de la version ','What is new in version ')+VERSION)
  d.set_detail(message)
  d.set_buttons([self.tr('Compris','Got it')])
  def done(dialog,result):
   try:
    dialog.choose_finish(result)
    acknowledged()
   except GLib.Error:pass
  d.choose(self,None,done)
  return False
 def on_key_pressed(self,_controller,keyval,_keycode,state):
  ctrl=bool(state & Gdk.ModifierType.CONTROL_MASK)
  alt=bool(state & Gdk.ModifierType.ALT_MASK)
  if keyval==Gdk.KEY_F11:self.toggle_fullscreen();return True
  if keyval==Gdk.KEY_Escape and self.is_fullscreen():self.unfullscreen();return True
  if ctrl and keyval in (Gdk.KEY_f,Gdk.KEY_F) and self._active_page=='Fichiers':self.search.grab_focus();return True
  if ctrl and keyval in (Gdk.KEY_r,Gdk.KEY_R) and self._active_page=='Fichiers':self.refresh();return True
  if ctrl and keyval in (Gdk.KEY_h,Gdk.KEY_H) and self._active_page=='Fichiers':self.hidden();return True
  if ctrl and keyval==Gdk.KEY_1:self.home();return True
  if ctrl and keyval==Gdk.KEY_2:self.downloads_page();return True
  if ctrl and keyval==Gdk.KEY_3:self.versions_page();return True
  if ctrl and keyval==Gdk.KEY_4:self.favorites_page();return True
  if ctrl and keyval==Gdk.KEY_5:self.settings_page();return True
  if ctrl and keyval==Gdk.KEY_6:self.shortcuts_page();return True
  if keyval==Gdk.KEY_F5 and self._active_page=='Fichiers':self.refresh();return True
  if alt and keyval==Gdk.KEY_Left and self._active_page=='Fichiers':self.go_back();return True
  if alt and keyval==Gdk.KEY_Right and self._active_page=='Fichiers':self.go_forward();return True
  return False
 def toggle_fullscreen(self,*_):
  if self.is_fullscreen():self.unfullscreen()
  else:self.fullscreen()
 def toggle_maximize(self,*_):
  if self.is_maximized():self.unmaximize()
  else:self.maximize()
 def smooth_scroll(self,scroller):
  # Animate discrete mouse-wheel steps; keep precise touchpad scrolling native.
  state={'target':None,'running':False}
  controller=Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
  def on_scroll(ctrl,dx,dy):
   if ctrl.get_unit()!=Gdk.ScrollUnit.WHEEL:return False
   adjustment=scroller.get_vadjustment()
   maximum=max(adjustment.get_lower(),adjustment.get_upper()-adjustment.get_page_size())
   if maximum<=adjustment.get_lower():return False
   current=adjustment.get_value()
   baseline=state['target'] if state['running'] else current
   state['target']=min(maximum,max(adjustment.get_lower(),baseline+dy*88))
   if not state['running']:
    state['running']=True
    def animate():
     value=adjustment.get_value();target=state['target']
     diff=target-value
     if abs(diff)<0.7:
      adjustment.set_value(target);state['running']=False;return False
     adjustment.set_value(value+diff*0.24)
     return True
    GLib.timeout_add(16,animate)
   return True
  controller.connect('scroll',on_scroll)
  scroller.add_controller(controller)
 def clear(self):
  # Create the next page without destroying the visible one: Gtk.Stack
  # crossfades two complete pages instead of fading newly inserted widgets.
  self._page_serial+=1
  old=self.page_stack.get_visible_child()
  content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
  for edge in ('top','bottom'):getattr(content,'set_margin_'+edge)(18)
  for edge in ('start','end'):getattr(content,'set_margin_'+edge)(20)
  content.set_hexpand(True);content.add_css_class('content-area')
  scroll=Gtk.ScrolledWindow(vexpand=True,hexpand=True)
  scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
  scroll.set_kinetic_scrolling(True)
  self.smooth_scroll(scroll)
  scroll.set_overlay_scrolling(True)
  scroll.set_child(content)
  self.page_stack.add_child(scroll)
  self.content=content;self.page_scroll=scroll;self._pending_old_page=old
  self._active_page=None
 def _animate_new_page(self):
  old=getattr(self,'_pending_old_page',None)
  new=self.page_scroll
  self.page_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE if self.animations else Gtk.StackTransitionType.NONE)
  self.page_stack.set_transition_duration(360 if self.animations else 0)
  self.page_stack.set_visible_child(new)
  self._pending_old_page=None
  # A delayed cleanup lets GTK finish the actual crossfade. Rapid navigation
  # is safe: all obsolete children except the current page are removed later.
  if old is not None:
   def cleanup():
    if old.get_parent() is self.page_stack and old is not self.page_stack.get_visible_child():
     self.page_stack.remove(old)
    return False
   GLib.timeout_add(440 if self.animations else 1,cleanup)
 def mark_page(self,name):
  self._active_page=name
  self._animate_new_page()
  for button,_icon,label in self.nav_buttons:
   if label==name:button.add_css_class('active-nav')
   else:button.remove_css_class('active-nav')

 def heading(self,text):
  # Every secondary page gets a short scenic header, with an accessible text overlay.
  banner=Gtk.Overlay();banner.add_css_class('section-banner');banner.set_size_request(-1,110)
  image=Gtk.Picture.new_for_filename(str(pathlib.Path(__file__).with_name('mountain-bg.png')))
  image.set_content_fit(Gtk.ContentFit.COVER);image.set_can_shrink(True)
  banner.set_child(image)
  overlay=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
  overlay.set_halign(Gtk.Align.START);overlay.set_valign(Gtk.Align.CENTER)
  overlay.set_margin_start(18);overlay.set_margin_end(12)
  label=Gtk.Label(label=text,xalign=0,wrap=True);label.add_css_class('section-banner-title');overlay.append(label)
  banner.add_overlay(overlay);self.content.append(banner)
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
  names={'Accueil':'Home','Fichiers':'Files','Corbeille':'Trash','Jeux & applis':'Games & apps','Nettoyage':'Cleanup','Détective stockage':'Storage inspector','Radar doublons':'Duplicates','Fichiers inutiles':'Unused files','Téléchargements':'Downloads','Favoris':'Favorites','Anciennes versions':'Previous versions','Mises à jour':'Updates','Paramètres':'Settings','Raccourcis':'Shortcuts'}
  for button,icon,name in self.nav_buttons:
   label=names.get(name,name) if self.language=='en' else name
   button.set_label((icon+'    ' if self.nav_style=='icons' else '')+label)
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
  self.clear();self.mark_page('Paramètres');self.heading(self.tr('PARAMÈTRES  ⚙','SETTINGS  ⚙'))
  self.info(self.tr('Personnalise ton application. Les changements sont enregistrés automatiquement.','Customize your app. Changes are saved automatically.'))
  self.info('Langue / Language')
  self.info('Certaines pages restent en français pendant la traduction. / Some pages are not translated yet.')
  language_row=Gtk.Box(spacing=8);self.content.append(language_row)
  self.btn(language_row,'Français',lambda *_:self.set_language('fr'))
  self.btn(language_row,'English',lambda *_:self.set_language('en'))
  self.info('NOUVEAU 27.4 — vraies transitions fondues entre les pages et mises à jour GitHub.')
  self.btn(self.content,'⬆ Vérifier les mises à jour',self.updates_page)
  self.info('1. Fond de l’application')
  bgrow=Gtk.FlowBox();bgrow.set_selection_mode(Gtk.SelectionMode.NONE);bgrow.set_max_children_per_line(3);bgrow.set_row_spacing(5);bgrow.set_column_spacing(6);self.content.append(bgrow)
  for label,val in [('✦ Aurore néon','aurora'),('Uni','solid'),('Nuit profonde','midnight')]:
   self.btn(bgrow,label,lambda _b,v=val:self.set_background_style(v))
  self.info('2. Espacement des éléments')
  densityrow=Gtk.FlowBox();densityrow.set_selection_mode(Gtk.SelectionMode.NONE);densityrow.set_max_children_per_line(3);densityrow.set_row_spacing(5);densityrow.set_column_spacing(6);self.content.append(densityrow)
  for label,val in [('Compact','compact'),('Confort','comfortable'),('Aéré','spacious')]:
   self.btn(densityrow,label,lambda _b,v=val:self.set_density(v))
  self.info('3. Style du menu latéral')
  navrow=Gtk.FlowBox();navrow.set_selection_mode(Gtk.SelectionMode.NONE);navrow.set_max_children_per_line(3);navrow.set_row_spacing(5);navrow.set_column_spacing(6);self.content.append(navrow)
  for label,val in [('Symboles + texte','icons'),('Texte seulement','text')]:
   self.btn(navrow,label,lambda _b,v=val:self.set_nav_style(v))
  self.info('Apparence')
  theme_row=Gtk.FlowBox();theme_row.set_selection_mode(Gtk.SelectionMode.NONE);theme_row.set_max_children_per_line(3);theme_row.set_row_spacing(5);theme_row.set_column_spacing(6);self.content.append(theme_row)
  self.info('Choisis ton thème avec les boutons ci-dessous :')
  for label,val in [('☀️ Clair','light'),('🌙 Sombre','dark'),('🌓 Système','system')]:
   self.btn(theme_row,label,lambda _b,v=val:self.set_theme(v))
  self.info('Couleur principale — choix actuel : '+self.accent)
  colors=Gtk.FlowBox();colors.set_selection_mode(Gtk.SelectionMode.NONE);colors.set_max_children_per_line(3);colors.set_row_spacing(5);colors.set_column_spacing(6);self.content.append(colors)
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
 def updates_page(self,*_):
  self.clear();self.mark_page('Mises à jour');self.heading('MISES À JOUR  ⬆')
  self.info('Version installée : '+VERSION)
  self.info('Vérification des versions officielles publiées sur GitHub. Aucun téléchargement automatique sans ton accord.')
  self.update_status=Gtk.Label(label='Clique sur Vérifier pour rechercher une nouvelle version.',xalign=0,wrap=True)
  self.content.append(self.update_status)
  self.update_button=self.btn(self.content,'🔎 Vérifier les mises à jour',self.check_updates)
  self.install_button=self.btn(self.content,'⬇ Télécharger et installer la mise à jour',self.download_update)
  self.install_button.set_sensitive(False)
  self.btn(self.content,'🌐 Voir les versions sur GitHub',lambda *_:Gio.AppInfo.launch_default_for_uri('https://github.com/eliott39pro39-png/gestion-des-stockage/releases',None))
 def _update_message(self,message,release=None):
  self._update_busy=False
  if release is not None:self._update_release=release
  if self._active_page=='Mises à jour':
   self.update_status.set_text(message)
   self.update_button.set_sensitive(True)
   self.install_button.set_sensitive(bool(self._update_release))
  return False
 def check_updates(self,*_):
  if self._update_busy:return
  self._update_busy=True;self._update_release=None
  self.update_status.set_text('Recherche de la dernière version officielle…')
  self.update_button.set_sensitive(False);self.install_button.set_sensitive(False)
  def worker():
   try:
    req=urllib.request.Request('https://api.github.com/repos/eliott39pro39-png/gestion-des-stockage/releases/latest',headers={'User-Agent':'GestionStockage/'+VERSION,'Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(req,timeout=12) as response:release=json.load(response)
    tag=release.get('tag_name','').lstrip('v')
    if not re.fullmatch(r'[0-9]+\.[0-9]+(?:\.[0-9]+)?',tag):raise ValueError('Version distante invalide.')
    def parts(v):return tuple(int(x) for x in v.split('.'))+(0,)*(3-len(v.split('.')))
    if parts(tag)<=parts(VERSION):
     GLib.idle_add(self._update_message,'Tu as déjà la dernière version officielle ('+VERSION+').');return
    filename='gestion-stockage-'+tag+'-all.deb'
    asset=next((a for a in release.get('assets',[]) if a.get('name')==filename),None)
    if not asset:raise ValueError('La nouvelle version ne contient pas de paquet Ubuntu .deb.')
    url=asset.get('browser_download_url','')
    if not url.startswith('https://github.com/eliott39pro39-png/gestion-des-stockage/releases/download/'):raise ValueError('Adresse du paquet inattendue.')
    GLib.idle_add(self._update_message,'Nouvelle version '+tag+' disponible ! Clique sur Télécharger et installer.',{'version':tag,'url':url,'filename':filename})
   except Exception as exc:GLib.idle_add(self._update_message,'Vérification impossible : '+str(exc))
  threading.Thread(target=worker,daemon=True).start()
 def download_update(self,*_):
  release=self._update_release
  if not release or self._update_busy:return
  self.dialog('Installer Gestion de stockage '+release['version']+' ?', 'Le paquet officiel sera téléchargé dans Téléchargements. Un terminal demandera ton mot de passe Ubuntu pour la mise à niveau.',lambda:self._start_update_download(release))
 def _start_update_download(self,release):
  if self._update_busy:return
  self._update_busy=True
  self.update_status.set_text('Téléchargement en cours…');self.update_button.set_sensitive(False);self.install_button.set_sensitive(False)
  def worker():
   try:
    target=HOME/'Téléchargements'
    if not target.is_dir():target=HOME/'Downloads'
    target.mkdir(parents=True,exist_ok=True)
    path=target/release['filename']
    temp=path.with_suffix('.deb.part')
    try:
     req=urllib.request.Request(release['url'],headers={'User-Agent':'GestionStockage/'+VERSION})
     with urllib.request.urlopen(req,timeout=45) as source,open(temp,'wb') as dest:
      shutil.copyfileobj(source,dest)
     if temp.stat().st_size<1024:raise ValueError('Téléchargement incomplet.')
     package=subprocess.run(['dpkg-deb','-f',str(temp),'Package'],capture_output=True,text=True,timeout=10,check=True).stdout.strip()
     version=subprocess.run(['dpkg-deb','-f',str(temp),'Version'],capture_output=True,text=True,timeout=10,check=True).stdout.strip()
     if package!='gestion-stockage' or version!=release['version']:raise ValueError('Le paquet téléchargé ne correspond pas à la version attendue.')
     temp.replace(path)
    finally:
     if temp.exists():temp.unlink()
    GLib.idle_add(self._launch_update_terminal,path)
   except Exception as exc:GLib.idle_add(self._update_message,'Téléchargement impossible : '+str(exc),release)
  threading.Thread(target=worker,daemon=True).start()
 def _launch_update_terminal(self,path):
  # sudo runs inside a visible terminal; the user remains in control.
  command='sudo apt install -- '+shlex.quote(str(path))+'; echo; read -p "Appuie sur Entrée pour fermer…"'
  terminal=shutil.which('x-terminal-emulator') or shutil.which('gnome-terminal')
  if terminal:
   try:
    if pathlib.Path(terminal).name=='gnome-terminal':subprocess.Popen([terminal,'--','bash','-c',command])
    else:subprocess.Popen([terminal,'-e','bash','-c',command])
    self._update_message('Paquet téléchargé : '+str(path)+' — suis les instructions du terminal pour terminer la mise à jour.',self._update_release)
    return False
   except OSError:pass
  self._update_message('Paquet téléchargé : '+str(path)+' — ouvre un terminal et lance : sudo apt install -- '+shlex.quote(str(path)),self._update_release)
  return False

 def downloads_dir(self):
  if sys.platform=='win32':
   folder=HOME/'Downloads'
   if folder.is_dir():return folder
  for name in ('Téléchargements','Downloads'):
   folder=HOME/name
   if folder.is_dir():return folder
  return HOME
 def downloads_page(self,*_):
  self.clear();self.mark_page('Téléchargements');self.heading('TÉLÉCHARGEMENTS  ⬇')
  self.info('Tes fichiers téléchargés et les nouveautés de Gestion de stockage, au même endroit.')
  self.btn(self.content,'📁 Ouvrir mon dossier Téléchargements',lambda *_:self.open_dir(self.downloads_dir())).add_css_class('primary-action')
  self.heading('MISES À JOUR — HISTORIQUE')
  self.info('Les mises à jour sont présentées ici pour information. Aucun téléchargement ni installation automatique.')
  for version,changes in RELEASES:
   card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5);card.add_css_class('release-card');self.content.append(card)
   title=Gtk.Label(label='Version '+version+('  •  Actuelle' if version==VERSION else ''),xalign=0);title.add_css_class('release-title');card.append(title)
   for change in changes:card.append(Gtk.Label(label='• '+change,xalign=0,wrap=True))
   if version!=VERSION:self.btn(card,'Voir dans les anciennes versions ↗',self.versions_page)
  self.heading('DOSSIER TÉLÉCHARGEMENTS')
  try:
   items=sorted(self.downloads_dir().iterdir(),key=lambda p:p.stat().st_mtime,reverse=True)[:12]
   for path in items:
    line=Gtk.Box(spacing=10);self.content.append(line)
    line.append(Gtk.Label(label=('▣ ' if path.is_dir() else '▤ ')+path.name,xalign=0,hexpand=True,ellipsize=3))
    self.btn(line,'Ouvrir',lambda _b,p=path:self.open_download_item(p))
   if not items:self.info('Aucun téléchargement récent.')
  except OSError as exc:self.info('Lecture du dossier impossible : '+str(exc))
 def open_download_item(self,path):
  if path.is_dir():self.open_dir(path)
  else:
   try:Gio.AppInfo.launch_default_for_uri(path.as_uri(),None)
   except Exception as exc:self.dialog('Ouverture impossible',str(exc))
 def versions_page(self,*_):
  self.clear();self.mark_page('Anciennes versions');self.heading('ANCIENNES VERSIONS  ◷')
  self.info('Retrouve les anciennes éditions conservées dans le paquet. Les versions récentes sont ajoutées automatiquement à la construction.')
  archive=pathlib.Path(__file__).resolve().parent/'versions'
  known_buggy={'26.8','26.8.2','26.8.3','26.8.4','26.8.5','26.8.6'}
  def version_key(name):
   return tuple(int(part) for part in name.split('.'))
  available=sorted((p for p in archive.iterdir() if p.is_dir() and re.fullmatch(r'[0-9]+(?:\.[0-9]+)*',p.name) and (p/'app.py').is_file()),key=lambda p:version_key(p.name),reverse=True) if archive.is_dir() else []
  for heading,items in [('VERSIONS PRÉCÉDENTES',[p for p in available if p.name not in known_buggy]),('VERSIONS AVEC PROBLÈMES CONNUS ⚠',[p for p in available if p.name in known_buggy])]:
   self.heading(heading)
   if not items:self.info('Aucune version archivée dans cette catégorie.')
   for directory in items:
    version=directory.name;script=directory/'app.py'
    row=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5);row.add_css_class('release-card');self.content.append(row)
    description=dict(RELEASES).get(version,['Archive locale'])[0]
    row.append(Gtk.Label(label='Version '+version+' — '+description,hexpand=True,xalign=0,wrap=True))
    if version in known_buggy:
     self.btn(row,'Ouvrir ⚠',lambda _b,p=script,v=version:self.dialog('Version avec problèmes connus','Cette version a rencontré des problèmes. Ouvrir quand même ?',lambda:self.launch_beta(p,v)))
    else:self.btn(row,'Ouvrir ↗',lambda _b,p=script,v=version:self.launch_beta(p,v))
 def launch_beta(self,script,version):
  log_path=HOME/'.cache/gestion-stockage-final/archive-launch.log'
  try:
   log_path.parent.mkdir(parents=True,exist_ok=True)
   log=log_path.open('w',encoding='utf-8')
   try:
    process=subprocess.Popen(['/usr/bin/python3',str(pathlib.Path(__file__).with_name('archive_launcher.py')),str(script),version],env={**os.environ,'GESTION_STOCKAGE_ARCHIVE_CHILD':'1'},start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
   finally:log.close()
   def check_launch():
    result=process.poll()
    if result is None:
     self.notify('Ancienne version lancée','Gestion de stockage '+version)
    else:
     try:details=log_path.read_text(encoding='utf-8')[-1800:]
     except OSError:details='Consulte le journal : '+str(log_path)
     self.dialog('Impossible de lancer la version '+version,details or 'Le programme a quitté immédiatement.')
    return False
   GLib.timeout_add(1200,check_launch)
  except OSError as exc:self.dialog('Impossible de lancer la version',str(exc))
 def about_page(self,*_):
  self.clear();self.heading('GESTION DE STOCKAGE — '+VERSION)
  self.info('27.4 — Transitions GTK4 croisées et téléchargement guidé des mises à jour officielles.')
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
  self.info('27.0 — Nouvel onglet Téléchargements, historique des versions, accès rapides, nouveau logo, effets légers et raccourcis.')
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
 def duplicates_page(self,*_):
  self.clear();self.mark_page('Doublons');self.heading('RADAR DES DOUBLONS  ◈')
  self.info('Analyse par contenu SHA-256. Aucun fichier sélectionné par défaut. Vérifie les chemins avant toute mise à la corbeille.')
  bar=Gtk.Box(spacing=7);self.content.append(bar)
  folder=Gtk.Entry(text=str(HOME),hexpand=True);bar.append(folder)
  self.btn(bar,'Rechercher',lambda *_:self.start_duplicates(folder.get_text()))
  self.btn(bar,'Annuler',lambda *_:getattr(self,'_duplicates_cancel',threading.Event()).set())
  self.duplicate_status=Gtk.Label(label='Choisis un dossier.',xalign=0,wrap=True);self.content.append(self.duplicate_status)
  self.duplicate_results=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5);self.content.append(self.duplicate_results)
  self.duplicate_checks=[];self.duplicate_groups=[]
  self.btn(self.content,'Mettre la sélection à la corbeille',self.trash_duplicates)
 def start_duplicates(self,path):
  if getattr(self,'_duplicates_busy',False):return
  root=pathlib.Path(path).expanduser()
  if not root.is_dir():self.duplicate_status.set_text('Dossier inaccessible.');return
  self._duplicates_busy=True;self._duplicates_cancel=threading.Event()
  self.duplicate_status.set_text('Analyse en cours, 30 000 fichiers maximum…')
  while child:=self.duplicate_results.get_first_child():self.duplicate_results.remove(child)
  self.duplicate_checks=[];self.duplicate_groups=[]
  def worker():
   sizes={};pending=[root];count=0;errors=0
   while pending and count<30000 and not self._duplicates_cancel.is_set():
    try:
     with os.scandir(pending.pop()) as entries:
      for item in entries:
       if self._duplicates_cancel.is_set() or count>=30000:break
       try:
        if item.is_symlink():continue
        if item.is_dir(follow_symlinks=False):pending.append(pathlib.Path(item.path))
        elif item.is_file(follow_symlinks=False):
         st=item.stat(follow_symlinks=False);count+=1
         if st.st_size:sizes.setdefault(st.st_size,[]).append(pathlib.Path(item.path))
       except OSError:errors+=1
    except OSError:errors+=1
   hashes={}
   for size,paths in sizes.items():
    if self._duplicates_cancel.is_set():break
    if len(paths)<2:continue
    for p in paths:
     if self._duplicates_cancel.is_set():break
     try:
      if p.is_symlink() or not p.is_file() or p.stat().st_size!=size:continue
      h=hashlib.sha256()
      with p.open('rb') as stream:
       while not self._duplicates_cancel.is_set():
        chunk=stream.read(1048576)
        if not chunk:break
        h.update(chunk)
      if not self._duplicates_cancel.is_set():hashes.setdefault((size,h.digest()),[]).append(p)
     except OSError:errors+=1
   groups=[(key[0],paths) for key,paths in hashes.items() if len(paths)>1]
   GLib.idle_add(self.finish_duplicates,groups,count,errors,bool(pending) or count>=30000 or self._duplicates_cancel.is_set())
  threading.Thread(target=worker,daemon=True).start()
 def finish_duplicates(self,groups,count,errors,partial):
  self._duplicates_busy=False
  if self._active_page!='Doublons':return False
  saving=sum(size*(len(paths)-1) for size,paths in groups)
  self.duplicate_status.set_text(f'{count} fichiers analysés · {len(groups)} groupes · jusqu’à {saving/1048576:.1f} Mo récupérables · {errors} erreurs'+(' · résultats partiels' if partial else ''))
  self.duplicate_groups=[paths for _size,paths in groups]
  for size,paths in groups:
   group=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3);group.add_css_class('release-card')
   group.append(Gtk.Label(label=f'{len(paths)} copies identiques · {size/1048576:.1f} Mo chacune',xalign=0))
   for p in paths:
    check=Gtk.CheckButton(label=str(p));group.append(check);self.duplicate_checks.append((check,p))
   self.duplicate_results.append(group)
  return False
 def trash_duplicates(self,*_):
  chosen=[p for check,p in getattr(self,'duplicate_checks',[]) if check.get_active()]

  if not chosen:self.dialog('Aucune sélection','Coche uniquement les copies à mettre à la corbeille.');return
  if any(all(p in chosen for p in group) for group in self.duplicate_groups):
   self.dialog('Sélection dangereuse','Conserve au moins une copie dans chaque groupe de doublons.');return
  self.dialog('Confirmer la mise à la corbeille',f'{len(chosen)} fichier(s) sélectionné(s). Les originaux non sélectionnés seront conservés.',lambda:self.execute_trash_duplicates(chosen))
 def execute_trash_duplicates(self,paths):
  done=0;errors=0
  for p in paths:
   try:
    if p.is_symlink() or not p.is_file():continue
    if sys.platform=='win32':
     from send2trash import send2trash
     send2trash(str(p))
    else:Gio.File.new_for_path(str(p)).trash(None)
    done+=1
   except Exception:errors+=1
  self.dialog('Résultat',f'{done} fichier(s) mis à la corbeille · {errors} erreur(s).')
  self.duplicates_page()
 def storage_detective(self,*_):
  """Read-only, bounded large-file inventory, on Linux and Windows."""
  self.clear();self.mark_page('Détective stockage');self.heading('DÉTECTIVE DE STOCKAGE  ◈')
  self.info('Découvre ce qui occupe vraiment ton disque : les 20 fichiers les plus volumineux du dossier choisi.')
  self.info('Analyse en lecture seule : aucun fichier supprimé, déplacé ou modifié. Les liens symboliques ne sont pas suivis.')
  controls=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8);self.content.append(controls)
  folder=Gtk.Entry(text=str(HOME),hexpand=True);controls.append(folder)
  self.btn(controls,'Analyser',lambda *_:self.start_storage_scan(folder.get_text()))
  self.btn(controls,'Annuler',lambda *_:self.cancel_storage_scan())
  self.storage_scan_status=Gtk.Label(label='Choisis un dossier et lance l’analyse.',xalign=0,wrap=True)
  self.content.append(self.storage_scan_status)
  self.storage_scan_results=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
  self.content.append(self.storage_scan_results)
 def cancel_storage_scan(self):
  if getattr(self,'_storage_scanning',False):
   self._storage_cancel.set()
   self.storage_scan_status.set_text('Annulation demandée…')
 def start_storage_scan(self,raw_path):
  if getattr(self,'_storage_scanning',False):
   self.storage_scan_status.set_text('Une analyse est déjà en cours.');return
  root=pathlib.Path(raw_path).expanduser()
  if not root.is_dir():
   self.storage_scan_status.set_text('Dossier introuvable ou inaccessible.');return
  self._storage_cancel=threading.Event()
  self._storage_scanning=True
  self.storage_scan_status.set_text('Analyse en cours (maximum 30 000 fichiers)…')
  while child:=self.storage_scan_results.get_first_child():self.storage_scan_results.remove(child)
  def worker():
   import heapq
   largest=[];count=0;errors=0;total=0;pending=[root]
   while pending and count<30000 and not self._storage_cancel.is_set():
    directory=pending.pop()
    try:
     with os.scandir(directory) as entries:
      for item in entries:
       if self._storage_cancel.is_set():break
       try:
        if item.is_symlink():continue
        if item.is_dir(follow_symlinks=False):
         pending.append(pathlib.Path(item.path));continue
        if not item.is_file(follow_symlinks=False):continue
        size=item.stat(follow_symlinks=False).st_size
        total+=size;count+=1
        if len(largest)<20:heapq.heappush(largest,(size,item.path))
        elif size>largest[0][0]:heapq.heapreplace(largest,(size,item.path))
        if count>=30000:break
       except (OSError,PermissionError):errors+=1
    except (OSError,PermissionError):errors+=1
   results=sorted(largest,reverse=True)
   GLib.idle_add(self.finish_storage_scan,root,results,count,total,errors,bool(pending) or count>=30000,self._storage_cancel.is_set())
  threading.Thread(target=worker,daemon=True).start()
 def finish_storage_scan(self,root,results,count,total,errors,limited,cancelled=False):
  self._storage_scanning=False
  if self._active_page!='Détective stockage':return False
  def pretty(n):
   for unit in ('o','Ko','Mo','Go','To'):
    if n<1024 or unit=='To':return f'{n:.1f} {unit}'
    n/=1024
  suffix=' — analyse annulée, résultats partiels' if cancelled else (' — limite de 30 000 fichiers atteinte, résultats partiels' if limited else '')
  self.storage_scan_status.set_text(f'{count} fichiers analysés · {pretty(total)} au total · {errors} accès impossibles'+suffix)
  if not results:self.info('Aucun fichier trouvé dans ce dossier.')
  for size,path in results:
   row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8);row.add_css_class('release-card')
   label=Gtk.Label(label=f'{pretty(size)}  ·  {path}',xalign=0,hexpand=True,wrap=True)
   row.append(label)
   self.btn(row,'Ouvrir le dossier',lambda _b,p=path:self.open_dir(pathlib.Path(p).parent))
   self.storage_scan_results.append(row)
  return False
 def home(self,*_):
  self.clear();self.mark_page('Accueil')
  hero=Gtk.Overlay();hero.set_size_request(-1,190);hero.add_css_class('hero');self.content.append(hero)
  picture=Gtk.Picture.new_for_filename(str(pathlib.Path(__file__).with_name('mountain-bg.png')))
  picture.set_content_fit(Gtk.ContentFit.COVER);picture.set_can_shrink(True);picture.set_hexpand(True);picture.set_vexpand(True);hero.set_child(picture)
  hero_text=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
  hero_text.set_halign(Gtk.Align.START);hero_text.set_valign(Gtk.Align.CENTER)
  hero_text.set_margin_start(24);hero_text.set_margin_end(12)
  label=Gtk.Label(label='Bienvenue !  ✦',xalign=0);label.add_css_class('hero-title');hero_text.append(label)
  subtitle=Gtk.Label(label='Gère, libère et organise ton espace de stockage facilement.',xalign=0,wrap=True)
  subtitle.add_css_class('hero-subtitle');hero_text.append(subtitle)
  version=Gtk.Label(label='VERSION '+VERSION,xalign=0);version.add_css_class('hero-version');hero_text.append(version)
  hero.add_overlay(hero_text)
  try:
   usage=shutil.disk_usage(HOME)
  except OSError as exc:
   self.info('Impossible de lire le disque : '+str(exc));return
  stats=Gtk.FlowBox();stats.set_selection_mode(Gtk.SelectionMode.NONE);stats.set_max_children_per_line(3);stats.set_row_spacing(10);stats.set_column_spacing(10);self.content.append(stats)
  for symbol,label,value in [('▣','Espace total',f'{usage.total/1e9:.1f} Go'),('◉','Espace utilisé',f'{usage.used/1e9:.1f} Go'),('◌','Espace libre',f'{usage.free/1e9:.1f} Go')]:
   card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5);card.add_css_class('dashboard-card');stats.append(card)
   title=Gtk.Label(label=symbol+'  '+label,xalign=0);title.add_css_class('dashboard-label');card.append(title)
   amount=Gtk.Label(label=value,xalign=0);amount.add_css_class('dashboard-value');card.append(amount)
  bar=Gtk.ProgressBar(fraction=usage.used/usage.total if usage.total else 0,show_text=True)
  bar.set_text(f'{usage.used/usage.total:.0%} utilisé' if usage.total else 'Disque inconnu');self.content.append(bar)
  if usage.total and usage.free/usage.total<.10:self.info('⚠️ Espace disque faible : moins de 10 % disponibles.')
  heading=Gtk.Label(label='Accès rapides',xalign=0);heading.add_css_class('dashboard-section');self.content.append(heading)
  quick=Gtk.FlowBox();quick.set_selection_mode(Gtk.SelectionMode.NONE);quick.set_max_children_per_line(3);quick.set_row_spacing(8);quick.set_column_spacing(8);self.content.append(quick)
  for label,path in [('⌂  Dossier personnel',HOME),('⬇  Téléchargements',self.downloads_dir()),('▤  Documents',HOME/'Documents'),('▣  Images',HOME/'Images'),('▶  Vidéos',HOME/'Vidéos'),('♫  Musique',HOME/'Musique')]:
   if path.is_dir():self.btn(quick,label,lambda _b,p=path:self.open_dir(p))
  actions=Gtk.Label(label='Outils',xalign=0);actions.add_css_class('dashboard-section');self.content.append(actions)
  tools=Gtk.FlowBox();tools.set_selection_mode(Gtk.SelectionMode.NONE);tools.set_max_children_per_line(3);tools.set_row_spacing(8);tools.set_column_spacing(8);self.content.append(tools)
  for label,callback in [('📁  Rangement intelligent',self.organizer_page),('▣  Explorateur',self.files),('◇  Jeux & applis',self.games),('✦  Nettoyage sécurisé',self.clean),('⬇  Téléchargements et mises à jour',self.downloads_page),('◷  Anciennes versions',self.versions_page),('★  Mes favoris',self.favorites_page)]:
   self.btn(tools,label,callback)
  self.info('F11 : plein écran • Échap : quitter le plein écran • Ctrl+2 : téléchargements')
 def files(self,*_):
  self.clear();self.mark_page('Fichiers')
  self.page_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.NEVER)
  self.content.set_vexpand(True)
  title=Gtk.Label(label=self.tr('Mes fichiers','My files'),xalign=0)
  title.add_css_class('heading');self.content.append(title)
  nav=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
  nav.add_css_class('file-toolbar');self.content.append(nav)
  self.btn(nav,'←',self.go_back)
  self.btn(nav,'→',self.go_forward)
  self.btn(nav,'↑',lambda *_:self.open_dir(self.cwd.parent))
  self.btn(nav,'⌂',lambda *_:self.open_dir(HOME))
  self.path=Gtk.Entry(text=str(self.cwd),hexpand=True)
  self.path.set_tooltip_text(self.tr('Chemin du dossier • Entrée pour ouvrir','Folder path • Press Enter to open'))
  self.path.connect('activate',lambda e:self.open_dir(pathlib.Path(e.get_text()).expanduser()))
  nav.append(self.path)
  quick=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6);self.content.append(quick)
  for name,paths in [('Téléchargements',['Téléchargements','Downloads']),('Documents',['Documents']),('Images',['Images','Pictures'])]:
   target=next((HOME/p for p in paths if (HOME/p).is_dir()),None)
   if target:self.btn(quick,name,lambda _b,p=target:self.open_dir(p))
  searchrow=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
  self.content.append(searchrow)
  self.search=Gtk.SearchEntry(placeholder_text=self.tr('Filtrer les fichiers de ce dossier…','Filter files in this folder…'))
  self.search.set_hexpand(True)
  self.search.connect('search-changed',lambda *_:self.refresh())
  searchrow.append(self.search)
  self.btn(searchrow,self.tr('Liste / grille','List / grid'),self.toggle_file_view)
  menu=Gtk.MenuButton(label=self.tr('⋯ Options','⋯ Options'))
  pop=Gtk.Popover()
  opts=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
  opts.set_margin_top(8);opts.set_margin_bottom(8)
  opts.set_margin_start(8);opts.set_margin_end(8)
  for label,cb in [('Nouveau dossier',self.mkdir),('Ajouter aux favoris',self.add_favorite),
                   ('Retirer des favoris',self.remove_favorite),('Afficher fichiers cachés',self.hidden),
                   ('Trier par nom',lambda *_:self.change_file_sort('name')),
                   ('Trier par taille',lambda *_:self.change_file_sort('size')),
                   ('Trier par date',lambda *_:self.change_file_sort('date')),
                   ('Copier le chemin',self.copy_current_folder_path)]:
   self.btn(opts,label,cb)
  pop.set_child(opts);menu.set_popover(pop);searchrow.append(menu)
  filters=Gtk.Box(spacing=5);self.content.append(filters)
  for label,key in [('Tous','all'),('Dossiers','folders'),('Images','images'),('Documents','documents')]:
   self.btn(filters,label,lambda _b,k=key:self.set_file_filter(k)).add_css_class('file-filter')
  self.count_label=Gtk.Label(xalign=0)
  self.count_label.add_css_class('file-count');self.content.append(self.count_label)
  scroll=Gtk.ScrolledWindow(vexpand=True,hexpand=True)
  scroll.set_min_content_height(240);self.content.append(scroll)
  self.listbox=Gtk.ListBox()
  self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
  self.listbox.connect('row-activated',self.activate_row)
  self.listbox.connect('row-selected',lambda *_:self.update_file_actions())
  self.file_grid=Gtk.FlowBox()
  self.file_grid.set_selection_mode(Gtk.SelectionMode.SINGLE)
  self.file_grid.set_min_children_per_line(2)
  self.file_grid.set_max_children_per_line(5)
  self.file_grid.set_column_spacing(8)
  self.file_grid.set_row_spacing(8)
  self.file_grid.connect('child-activated',lambda _box,child:self.open_dir(child.path) if child.path.is_dir() else self.open_file_path(child.path))
  self.file_grid.connect('selected-children-changed',lambda *_:self.update_file_actions())
  scroll.set_child(self.file_grid if self.file_view=='grid' else self.listbox)
  actions=Gtk.Box(spacing=6);actions.add_css_class('file-actions')
  self.content.append(actions);self.file_actions=actions
  self.btn(actions,'Ouvrir',self.open_selected)
  self.btn(actions,'Renommer',self.rename)
  self.btn(actions,'Copier',lambda *_:self.choose_destination(False))
  self.btn(actions,'Déplacer',lambda *_:self.choose_destination(True))
  extra=Gtk.MenuButton(label='⋯ Plus')
  extra_pop=Gtk.Popover()
  extra_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
  extra_box.set_margin_top(8);extra_box.set_margin_bottom(8)
  extra_box.set_margin_start(8);extra_box.set_margin_end(8)
  self.btn(extra_box,'Copier le chemin',self.copy_selected_path)
  self.btn(extra_box,'Mettre à la corbeille',self.trash)
  danger=self.btn(extra_box,'Supprimer définitivement',self.delete)
  danger.add_css_class('danger-action')
  extra_pop.set_child(extra_box);extra.set_popover(extra_pop)
  actions.append(extra);actions.set_visible(False)
  self.refresh()
 def toggle_file_view(self,*_):
  self.file_view='grid' if self.file_view=='list' else 'list';self.save_prefs();self.files()
 def set_file_filter(self,key):
  self.file_filter=key;self.refresh()
 def update_file_actions(self):
  if hasattr(self,'file_actions'):self.file_actions.set_visible(self.selected() is not None)
 def organizer_page(self,*_):
  self.clear();self.mark_page('Rangement');self.heading('📁 RANGEMENT INTELLIGENT')
  self.info('Prévisualise les déplacements avant de les autoriser. Aucun fichier supprimé. Les sous-dossiers restent intacts.')
  folder=Gtk.Entry(text=str(self.downloads_dir()),hexpand=True);self.content.append(folder)
  preview=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=7);self.content.append(preview)
  state={'plan':[],'done':[]}
  def reset():
   while preview.get_first_child():preview.remove(preview.get_first_child())
  def prepare(*_):
   reset();state['plan']=[]
   try:state['plan']=smart_organizer.plan(folder.get_text())
   except (OSError,ValueError) as exc:self.info(str(exc));return
   moves=state['plan']
   if not moves:self.info('🎉 Aucun fichier à ranger ici.');return
   self.info(f'🔎 {len(moves)} fichier(s) à ranger. Vérifie la liste :')
   for source,target in moves:
    line=Gtk.Label(label=f'📄 {source.name}  →  📁 {target.parent.name}/',xalign=0,wrap=True)
    preview.append(line)
   self.btn(preview,'✅ Confirmer les déplacements',lambda *_:self.dialog('Ranger ces fichiers ?',f'{len(moves)} fichiers seront déplacés dans des sous-dossiers. Tu pourras annuler immédiatement.',apply))
  def apply():
   try:state['done']=smart_organizer.execute(state['plan'])
   except OSError as exc:self.dialog('Erreur de rangement',str(exc));return
   reset();self.info(f'🎉 {len(state["done"])} fichier(s) rangé(s).')
   if state['done']:self.btn(preview,'↩️ Annuler ce rangement',revert)
  def revert(*_):
   try:restored=smart_organizer.undo(state['done'])
   except OSError as exc:self.dialog('Annulation impossible',str(exc));return
   reset();self.info(f'↩️ {len(restored)} fichier(s) remis à leur place.')
   state['done']=[]
  self.btn(self.content,'🔎 Prévisualiser le rangement',prepare)
  self.info('Catégories : Images, Vidéos, Musique, Documents et Archives. Les fichiers inconnus sont laissés en place.')
 def assistant_page(self,*_):
  self.clear();self.mark_page('Assistant');self.heading(self.tr('DISCUTE AVEC TON ASSISTANT  🤖','CHAT WITH YOUR ASSISTANT  🤖'))
  self.info(self.tr('Salut !! 👋💙 Écris-moi ce que tu cherches. Je te répondrai comme dans une conversation ! 🤖','Hi! 👋💙 Tell me what you are looking for. I will help you find it! 🤖'))
  folder=Gtk.Entry(text=str(HOME),hexpand=True);self.content.append(folder)
  self.info(self.tr('Dossier dans lequel rechercher (tu peux changer ce chemin) :','Folder to search in (you can change this path):'))
  status=Gtk.Label(label=self.tr('🤖 Salut !! 👋💙 Écris ta demande ci-dessous !','🤖 Hi! 👋💙 Type your request below!'),xalign=0,wrap=True);self.content.append(status)
  scroller=Gtk.ScrolledWindow(vexpand=True,min_content_height=280)
  scroller.set_kinetic_scrolling(True)
  self.content.append(scroller)
  results=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=9)
  results.set_margin_top(12);results.set_margin_bottom(12)
  scroller.set_child(results)
  history=assistant_history.load_history()
  if not isinstance(history,list):history=[]
  def speak(message,user=False,save=True):
   if save:
    history.append({'user':bool(user),'message':str(message)})
    try:assistant_history.save_history(history)
    except OSError:pass
   row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
   row.set_halign(Gtk.Align.END if user else Gtk.Align.START)
   label=Gtk.Label(label=('🧑  ' if user else '🤖  ')+message,xalign=0,wrap=True,selectable=True)
   label.set_max_width_chars(76)
   label.set_margin_top(8);label.set_margin_bottom(8)
   label.set_margin_start(12);label.set_margin_end(12)
   label.add_css_class('card')
   row.append(label);results.append(row)
   GLib.idle_add(lambda:scroller.get_vadjustment().set_value(scroller.get_vadjustment().get_upper()) or False)
   return False
  composer=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8);self.content.append(composer)
  message_entry=Gtk.Entry(placeholder_text=self.tr('💬 Ex : Trouve War Thunder','💬 E.g. Find War Thunder'),hexpand=True)
  composer.append(message_entry)
  def clear_results():
   pass  # Preserve conversation history
  def find(mode):
   clear_results()
   self.prompt('Assistant — rechercher','Nom du fichier ou dossier', '',lambda query:run_search(mode,query))
  search_state={'cancel':None,'running':False}
  search_status=Gtk.Label(label=self.tr('Prêt à rechercher','Ready to search'),xalign=0,wrap=True)
  self.content.append(search_status)
  def run_search(mode,query):
   if search_state['cancel'] is not None:
    search_state['cancel'].set()
   cancel=threading.Event()
   search_state['cancel']=cancel
   search_state['running']=True
   search_status.set_text('🔎 Recherche en cours… 0 éléments analysés')
   speak('🔎 Je cherche « '+query+' »…')
   raw_folder=folder.get_text()
   def update_progress(count,path):
    GLib.idle_add(lambda: search_status.set_text(
     f'🔎 {count} éléments analysés • {path}' if search_state['cancel'] is cancel else search_status.get_text()) or False)
   def done(found,partial):
    if search_state['cancel'] is not cancel:return False
    search_state['running']=False
    search_status.set_text('✓ Recherche terminée'+(' (limite atteinte)' if partial else ''))
    return show_found(mode,found,partial)
   def failure(exc):
    if search_state['cancel'] is not cancel:return False
    search_state['running']=False
    search_status.set_text('⚠️ Recherche interrompue')
    return speak('😕 Recherche impossible : '+str(exc))
   def worker():
    try:
     found,partial=assistant_tools.search_items(raw_folder,query,progress=update_progress,cancel=cancel)
     GLib.idle_add(done,found,partial)
    except Exception as exc:GLib.idle_add(failure,exc)
   threading.Thread(target=worker,daemon=True).start()
  self.btn(self.content,'⏹ Annuler la recherche',lambda *_:search_state['cancel'].set() if search_state['cancel'] else None)
  def show_found(mode,found,partial):
   if found:speak(f'OUI !! 🎉 J’ai trouvé {len(found)} fichier(s) ou dossier(s) correspondant à ta recherche !'+(' ⚠️ Recherche partielle.' if partial else '')+' 👇')
   else:speak('😕 Aucun résultat. Essaie un autre nom ou dossier !')
   for path in found:
    line=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=7);results.append(line)
    label=Gtk.Label(label=('📁 ' if path.is_dir() else '📄 ')+str(path),xalign=0,wrap=True,hexpand=True);line.append(label)
    if mode=='rename' and path.is_file():
     self.btn(line,'Renommer…',lambda _b,p=path:ask_rename(p))
    elif path.is_dir():
     self.btn(line,'Ouvrir',lambda _b,p=path:self.open_dir(p))
   return False
  def ask_rename(path):
   self.prompt('Assistant — renommer','Nouveau nom pour '+path.name,path.name,lambda name:confirm(path,name))
  def confirm(path,name):
   try:source,target=assistant_tools.preview_rename(path,name)
   except Exception as exc:self.dialog('Renommage impossible',str(exc));return
   if not source.is_file():self.dialog('Non pris en charge','Le renommage guidé accepte uniquement les fichiers.');return
   self.dialog('C’est bien ce fichier ?',f'Fichier : {source}\nNouveau nom : {target.name}\nAucun autre fichier ne sera remplacé.',lambda:self.perform(lambda:assistant_tools.confirm_rename(source,target),'Fichier renommé'))
  def send(*_):
   message=message_entry.get_text().strip()
   if not message:return
   message_entry.set_text('')
   speak(message,True)
   lower=message.casefold()
   if 'doublon' in lower:speak('📋 Bien sûr ! Je t’ouvre le radar des doublons !');self.duplicates_page();return
   if 'gros fichier' in lower or 'espace disque' in lower:speak('💾 Allons voir les gros fichiers !');self.storage_detective();return
   if 'ranger' in lower or 'organiser' in lower:speak('📁 Le rangement automatique arrive bientôt ! Je ne touche à rien sans ton accord. 💙');return
   if lower.startswith(('renomme ', 'renommer ')):
    query=message.split(' ',1)[1].strip()
    for prefix in ('le fichier ', 'un fichier ', 'le dossier ', 'un dossier '):
     if query.casefold().startswith(prefix):query=query[len(prefix):].strip()
    query=query.strip(' :«»"')
    if query:run_search('rename',query)
    else:speak('✏️ Quel fichier veux-tu renommer ? Exemple : Renomme test.txt')
    return
   if lower.startswith(('trouve ', 'trouver ', 'cherche ', 'chercher ', 'recherche ', 'rechercher ', 'retrouve ', 'retrouver ', 'montre ', 'affiche ')):
    query=message.split(' ',1)[1].strip()
    for prefix in ('le fichier ', 'un fichier ', 'le dossier ', 'un dossier '):
     if query.casefold().startswith(prefix):query=query[len(prefix):].strip()
    query=query.strip(' :«»"')
    if query:run_search('search',query)
    else:speak('🔎 Dis-moi le nom du fichier à chercher !')
    return
   if any(word in lower for word in ('fichier','fichiers','photo','photos','image','images','pdf','document','documents','vidéo','vidéos')):\n    run_search('search',message);return\n   if lower in ('salut','bonjour','hello','coucou','hey'):speak('Coucou !! 👋💙 Je suis prêt à t’aider !');return
   speak('🤔 Je ne comprends pas encore cette demande. Essaie « Trouve War Thunder », « Renomme test.txt » ou « Doublons » ! 💙')
  self.btn(composer,'➤ Envoyer',send)
  message_entry.connect('activate',send)
  if history:
   for item in history[-500:]:
    if isinstance(item,dict) and isinstance(item.get('message'),str):speak(item['message'],bool(item.get('user')),False)
  else:speak('Salut !! 👋💙 Dis-moi quel fichier tu cherches ! Par exemple : « Trouve War Thunder » 🔎')
  def erase_history(*_):
   def confirmed():
    history.clear()
    try:assistant_history.clear_history()
    except OSError:pass
    while results.get_first_child():results.remove(results.get_first_child())
    speak('💙 Historique effacé. Nouvelle conversation !')
   self.dialog('Effacer la conversation ?', 'Tous les messages enregistrés sur cet ordinateur seront supprimés.', confirmed)
  self.btn(self.content,'🗑️ Effacer l’historique du chat',erase_history)
  self.btn(self.content,'🔎 Rechercher un fichier ou dossier',lambda *_:find('search'))
  self.btn(self.content,'✏️ Renommer un fichier',lambda *_:find('rename'))
  self.btn(self.content,'📁 Ranger mes fichiers',self.organizer_page)
  self.btn(self.content,'💾 Trouver les gros fichiers',lambda *_:self.storage_detective())
  self.btn(self.content,'📋 Rechercher les doublons',lambda *_:self.duplicates_page())
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
 def remove_favorite(self,*_):
  fav=self.prefs.get('favorites',[])
  if str(self.cwd) in fav:
   fav.remove(str(self.cwd));self.save_prefs()
  self.files()
 def copy_current_folder_path(self,*_):
  try:
   display=Gdk.Display.get_default()
   if display is None:raise RuntimeError('Presse-papiers indisponible')
   display.get_clipboard().set(str(self.cwd))
   self.notify('Chemin du dossier copié',str(self.cwd))
  except Exception as exc:self.dialog('Copie impossible',str(exc))
 def favorites_page(self,*_):
  self.clear();self.mark_page('Favoris');self.heading('MES FAVORIS  ★')
  self.info('Tes dossiers favoris, accessibles en un clic. Les retirer des favoris ne supprime jamais les dossiers.')
  favorites=list(dict.fromkeys(self.prefs.get('favorites',[])))
  if not favorites:self.info('Aucun favori pour le moment. Dans Fichiers, clique sur « ⭐ Favori » pour en ajouter.')
  for item in favorites:
   folder=pathlib.Path(item)
   card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6);card.add_css_class('release-card');self.content.append(card)
   name=Gtk.Label(label=folder.name or str(folder),xalign=0,wrap=True);name.add_css_class('release-title');card.append(name)
   path_label=Gtk.Label(label=str(folder),xalign=0,wrap=True);card.append(path_label)
   actions=Gtk.FlowBox();actions.set_selection_mode(Gtk.SelectionMode.NONE);actions.set_max_children_per_line(2);actions.set_column_spacing(6);card.append(actions)
   if folder.is_dir():self.btn(actions,'Ouvrir',lambda _b,p=folder:self.open_dir(p))
   else:card.append(Gtk.Label(label='Dossier introuvable',xalign=0))
   self.btn(actions,'Retirer des favoris',lambda _b,p=item:self.remove_favorite_entry(p))
 def remove_favorite_entry(self,path):
  fav=self.prefs.get('favorites',[])
  if path in fav:fav.remove(path);self.save_prefs()
  self.favorites_page()
 def copy_selected_path(self,*_):
  path=self.selected()
  if path is None:return
  try:
   display=Gdk.Display.get_default()
   if display is None:raise RuntimeError('Presse-papiers indisponible')
   display.get_clipboard().set(str(path))
   self.notify('Chemin copié',str(path))
  except Exception as exc:self.dialog('Copie impossible',str(exc))
 def shortcuts_page(self,*_):
  self.clear();self.mark_page('Raccourcis')
  self.heading('⌨  Raccourcis clavier')
  self.info('Toutes les commandes utiles pour naviguer rapidement.')
  for key,description in [('F11','Activer ou quitter le plein écran'),('Échap','Quitter le plein écran'),('Ctrl + F','Rechercher dans les fichiers'),('Ctrl + R','Actualiser les fichiers'),('Ctrl + H','Afficher ou masquer les fichiers cachés'),('Alt + ← / →','Reculer ou avancer dans les dossiers'),('Ctrl + 1','Accueil'),('Ctrl + 2','Téléchargements'),('Ctrl + 3','Anciennes versions'),('F5','Actualiser l’explorateur'),('Ctrl + 4','Favoris'),('Ctrl + 5','Paramètres'),('Ctrl + 6','Raccourcis')]:
   line=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=14);line.add_css_class('release-card');self.content.append(line)
   k=Gtk.Label(label=key,xalign=0);k.set_size_request(125,-1);k.add_css_class('release-title');line.append(k)
   d=Gtk.Label(label=description,xalign=0,wrap=True,hexpand=True);line.append(d)
  self.btn(self.content,'← Retour à l’accueil',self.home)
 def hidden(self,*_):self.show_hidden=not self.show_hidden;self.save_prefs();self.refresh()
 def change_file_sort(self,mode):
  if self.file_sort==mode:self.file_sort_reverse=not self.file_sort_reverse
  else:self.file_sort=mode;self.file_sort_reverse=False
  self.refresh()
 def refresh(self):
  if self._active_page!='Fichiers' or not hasattr(self,'listbox'):return
  while child:=self.listbox.get_first_child():self.listbox.remove(child)
  while child:=self.file_grid.get_first_child():self.file_grid.remove(child)
  try:entries=list(self.cwd.iterdir())
  except OSError as e:self.dialog('Lecture impossible',str(e));return
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
  filters={'all':self.tr('Tous','All'),'folders':self.tr('Dossiers','Folders'),'images':self.tr('Images','Images'),'documents':self.tr('Documents','Documents')}
  sorts={'name':self.tr('nom','name'),'size':self.tr('taille','size'),'date':self.tr('date','date')}
  self.count_label.set_text(f'{len(self.entries)} '+self.tr('élément(s)','item(s)')+'  ·  '+filters[self.file_filter]+'  ·  '+self.tr('Tri : ','Sort: ')+sorts[self.file_sort])
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
   row.set_child(line);row.path=p
   if self.file_view=='grid':
    tile=Gtk.FlowBoxChild();tile.path=p
    panel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5)
    panel.set_size_request(125,94)
    panel.set_margin_top(9);panel.set_margin_bottom(9);panel.set_margin_start(8);panel.set_margin_end(8)
    symbol=Gtk.Label(label='📁' if is_dir else '📄');symbol.add_css_class('file-symbol');panel.append(symbol)
    label=Gtk.Label(label=p.name,wrap=True,ellipsize=3,max_width_chars=18,lines=2);panel.append(label)
    tile.set_child(panel);self.file_grid.append(tile)
   else:self.listbox.append(row)
 def open_file_path(self,path):
  try:Gio.AppInfo.launch_default_for_uri(path.as_uri(),None)
  except Exception as exc:self.dialog('Ouverture impossible',str(exc))
 def activate_row(self,_list,row):
  if row.path.is_dir():self.open_dir(row.path)
  else:self.open_file_path(row.path)
 def selected(self):
  row=(self.file_grid.get_selected_children()[0] if self.file_grid.get_selected_children() else None) if self.file_view=='grid' else self.listbox.get_selected_row();return row.path if row else None
 def open_selected(self,*_):
  p=self.selected()
  if p:
   if p.is_dir():self.open_dir(p)
   else:self.open_file_path(p)
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
  if getattr(self,'_operation_busy',False):
   self.dialog('Opération en cours','Attends la fin de la copie ou du déplacement.');return
  self._operation_busy=True
  def worker():
   error=None
   try:func()
   except Exception as exc:error=str(exc)
   GLib.idle_add(self.finish_operation,success,error)
  threading.Thread(target=worker,daemon=True).start()
 def finish_operation(self,success,error):
  self._operation_busy=False
  if error:self.dialog('Opération impossible',error)
  else:
   if self._active_page=='Fichiers':self.refresh()
   self.notify('Gestion de stockage',success)
   self.dialog('Terminé',success)
  return False
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
 def __init__(self):super().__init__(application_id='io.github.gestionstockage.Final',flags=Gio.ApplicationFlags.FLAGS_NONE)
 def do_activate(self):
  windows=self.get_windows()
  if windows:
   windows[0].present()
   return
  Window(self).present()
if __name__=='__main__':sys.exit(App().run(sys.argv))
