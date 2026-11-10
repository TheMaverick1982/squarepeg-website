/**
 * Square Peg Labs -> Google Sheet.
 *
 * Pulls every new build out of Supabase and files it on its own tab: Pizzas,
 * Pastas, Sandwiches, Salads, Drinks. One row per entry. The columns on each
 * tab come from that bench's own questions, so the Drinks tab has Base, Mixer,
 * Fruit, Garnish and Rim and the Pizzas tab has Sauce, Cheese, Toppings and
 * Finish -- which means you can sort the Pizzas tab by topping and the Drinks
 * tab by base, which you could not do if they shared one sheet.
 *
 * It only ever appends. A row that is already here is never rewritten,
 * reordered or removed, so Picked, Picked by, Ran and Notes stay with the
 * build they belong to. Nothing is written back to Supabase: the sheet owns
 * those four columns and they live here and nowhere else.
 *
 * SET IT UP
 *  1. Open the sheet. Extensions > Apps Script. Paste this over Code.gs.
 *  2. Project Settings > Script properties, add two (three if the project is
 *     standalone rather than opened from the sheet -- see book_() below):
 *       LAB_EXPORT_URL   https://<project>.supabase.co/functions/v1/lab-export
 *       LAB_EXPORT_KEY   the same string you set as LAB_EXPORT_KEY in Supabase
 *     They go here rather than in the code so the key is not in the file, and
 *     not in anyone's screenshot of it.
 *  3. Run `setUpTabs`, then `pullLabs`, approving the permission prompt.
 *     setUpTabs is safe to re-run: it adds whatever is missing, including
 *     the edit trigger and tickboxes on rows pulled before it existed.
 *  4. Triggers (the clock icon) > Add trigger > pullLabs > Time-driven >
 *     Day timer > whatever hour suits. Hourly is fine too; it is a small call.
 *
 * If a tab is ever deleted, delete the matching row in the Sync sheet and the
 * next run rebuilds the tab from the beginning.
 */

var TABS = {
  'pizza-lab': 'Pizzas',
  'pasta-lab': 'Pastas',
  'sandwich-lab': 'Sandwiches',
  'salad-lab': 'Salads',
  'bar-lab': 'Drinks'
};

/* What each bench asks, in order, so setUpTabs() can lay out all five before
   a single entry exists. The script does not depend on this being right: a
   label it has never seen is added as a column when the first build carrying
   it arrives. It is here so the sheet looks like a sheet on day one.
   Regenerate with: python3 -c "import sys;sys.path.insert(0,'data');import labs;
   print({b['slug']:[g['legend'] for g in b['groups']] for b in labs.BUILDERS})" */
var LABELS = {
  'pizza-lab': ['Sauce', 'Cheese', 'Toppings', 'Finish'],
  'pasta-lab': ['Pasta', 'Sauce', 'Protein', 'Add-ins', 'Finish'],
  'sandwich-lab': ['Roll or wrap', 'Protein', 'Cheese', 'Greens', 'Pile it on', 'Sauce or dressing'],
  'salad-lab': ['Greens', 'Protein', 'Cheese', 'On top', 'Dressing'],
  'bar-lab': ['Base', 'Mixer', 'Fruit', 'Garnish', 'Rim'],
};

// Written by people, never by this script. They sit to the right of the build
// columns, and a new question on a bench is inserted before them so that a
// note never ends up against the wrong row.
var MINE = ['Picked', 'Picked by', 'Ran (month)', 'Notes'];
var PICKED = 'Picked';
var FIRST = ['Date', 'Called', 'Built by'];
var SYNC = 'Sync';

/* Normally this script is bound to the sheet (Extensions > Apps Script) and
   getActiveSpreadsheet() is the sheet it lives in. Google's bootstrap for a
   bound script goes through script.google.com/accounts, and on an account
   whose multi-login chain is broken that hop dies with "Sorry, unable to open
   the file at this time" -- which is where this one ended up. A standalone
   project opens fine; it just has no sheet of its own, so it is told which one
   to use with a SHEET_ID script property (the long string in the sheet's URL
   between /d/ and /edit). Set it and the script is standalone; leave it off
   and it behaves exactly as a bound script. Same file either way. */
function book_() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  return id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
}

/**
 * Run this once, before anything has been submitted, to lay out all five tabs
 * with their columns. Without it the tabs appear one at a time, as the first
 * build for each bench lands, which is correct but looks like something is
 * broken on day one.
 */
function setUpTabs() {
  var book = book_();
  Object.keys(TABS).forEach(function (kind) {
    var sh = book.getSheetByName(TABS[kind]);
    if (!sh) {
      sh = book.insertSheet(TABS[kind]);
      sh.appendRow(['Id'].concat(FIRST, LABELS[kind] || [], MINE));
      sh.getRange(1, 1, 1, sh.getLastColumn()).setFontWeight('bold');
      sh.setFrozenRows(1);
      sh.hideColumns(1);
      sh.autoResizeColumns(2, sh.getLastColumn() - 1);
    }
    // Rows pulled before the tickbox existed have an empty text cell where the
    // box should be. Re-running this is how they get one, so everything below
    // is safe on a tab that is already set up.
    ensurePicked_(sh);
  });
  // Sync is bookkeeping, not a bench: it belongs after them, wherever it
  // happened to get created.
  var sync = book.getSheetByName(SYNC);
  if (sync) {
    book.setActiveSheet(sync);
    book.moveActiveSheet(book.getSheets().length);
    var first = book.getSheetByName(TABS[Object.keys(TABS)[0]]);
    if (first) book.setActiveSheet(first);
  }
  installEditTrigger_();
  // The blank one Google starts every new spreadsheet with.
  var first = book.getSheetByName('Sheet1');
  if (first && first.getLastRow() === 0 && book.getSheets().length > 1) {
    book.deleteSheet(first);
  }
}

function ensurePicked_(sh) {
  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var col = head.indexOf(PICKED) + 1;
  var n = sh.getLastRow() - 1;
  if (!col || n < 1) return;
  sh.getRange(2, col, n, 1).insertCheckboxes();
}

function pullLabs() {
  var props = PropertiesService.getScriptProperties();
  var url = props.getProperty('LAB_EXPORT_URL');
  var key = props.getProperty('LAB_EXPORT_KEY');
  if (!url || !key) throw new Error('Set LAB_EXPORT_URL and LAB_EXPORT_KEY in Script properties.');

  var book = book_();
  var since = lastSeen_(book);
  var q = url + '?key=' + encodeURIComponent(key) +
          (since ? '&since=' + encodeURIComponent(since) : '');

  var res = UrlFetchApp.fetch(q, { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) {
    throw new Error('lab-export said ' + res.getResponseCode() + ': ' + res.getContentText().slice(0, 200));
  }
  var entries = JSON.parse(res.getContentText()).entries || [];
  if (!entries.length) return 0;

  // Group first so each tab is opened and written once rather than once per
  // row. Apps Script is slow at this and a weekly pull can be a few hundred.
  var groups = {};
  entries.forEach(function (e) {
    var kind = e.kind || 'pizza-lab';
    (groups[kind] = groups[kind] || []).push(e);
  });

  var newest = since || '';
  Object.keys(groups).forEach(function (kind) {
    writeTab_(book, kind, groups[kind]);
    groups[kind].forEach(function (e) {
      if (e.created_at > newest) newest = e.created_at;
    });
  });

  setLastSeen_(book, newest);
  return entries.length;
}

function writeTab_(book, kind, entries) {
  var title = TABS[kind] || kind;
  var sh = book.getSheetByName(title);
  if (!sh) {
    sh = book.insertSheet(title);
    sh.appendRow(['Id'].concat(FIRST, MINE));
    sh.getRange(1, 1, 1, sh.getLastColumn()).setFontWeight('bold');
    sh.setFrozenRows(1);
    sh.hideColumns(1); // the id, kept for the dedupe below and nothing else
  }

  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];

  // Every label this batch uses, in the order the page asks them, inserted
  // before the human columns. Normally a no-op: the questions only change when
  // the kitchen list changes.
  entries.forEach(function (e) {
    (e.build || []).forEach(function (p) {
      if (head.indexOf(p.label) !== -1) return;
      var at = head.indexOf(MINE[0]);
      if (at === -1) at = head.length;
      sh.insertColumnBefore(at + 1);
      sh.getRange(1, at + 1).setValue(p.label).setFontWeight('bold');
      head.splice(at, 0, p.label);
    });
  });

  // An id already on the tab means a re-run, or a `since` reset. Skip it
  // rather than writing the build twice under someone's notes.
  var seen = {};
  var n = sh.getLastRow() - 1;
  if (n > 0) {
    sh.getRange(2, 1, n, 1).getValues().forEach(function (r) { seen[r[0]] = true; });
  }

  var rows = [];
  entries.forEach(function (e) {
    if (seen[e.id]) return;
    var row = new Array(head.length).fill('');
    row[0] = e.id;
    row[head.indexOf('Date')] = new Date(e.created_at);
    row[head.indexOf('Called')] = e.name || '';
    row[head.indexOf('Built by')] = e.by_name || '';
    (e.build || []).forEach(function (p) {
      var at = head.indexOf(p.label);
      if (at === -1) return;
      row[at] = Array.isArray(p.value) ? p.value.join(', ') : (p.value || '');
    });
    rows.push(row);
  });
  if (!rows.length) return;

  var at = sh.getLastRow() + 1;
  sh.getRange(at, 1, rows.length, head.length).setValues(rows);
  sh.getRange(2, head.indexOf('Date') + 1, sh.getLastRow() - 1, 1)
    .setNumberFormat('ddd d mmm yyyy');
  // A real tickbox, not the word "yes". One click, and onLabEdit drops the row
  // to the bottom so the top of the tab is only ever what still needs reading.
  var pick = head.indexOf(PICKED);
  if (pick !== -1) sh.getRange(at, pick + 1, rows.length, 1).insertCheckboxes();
  sh.autoResizeColumns(2, head.length - 1);
}

/* The high-water mark lives on its own tab rather than in script properties so
   that it is visible: if the pull ever looks wrong, you can see what it last
   asked for, and clear the cell to pull everything again. */
function lastSeen_(book) {
  var sh = book.getSheetByName(SYNC);
  return sh ? String(sh.getRange('B1').getValue() || '') : '';
}

function setLastSeen_(book, iso) {
  var sh = book.getSheetByName(SYNC);
  if (!sh) {
    sh = book.insertSheet(SYNC);
    sh.getRange('A1').setValue('Newest build pulled').setFontWeight('bold');
    sh.getRange('A2').setValue('Last run').setFontWeight('bold');
    sh.getRange('A4').setValue(
      'Clear B1 to pull every build again. Nothing already on a tab is written twice.');
  }
  // Plain text, forced. Sheets will happily turn an ISO timestamp into a date
  // value, and then this comes back out as "Mon Nov 10 2026 ..." and the next
  // pull asks the function for a `since` it cannot use.
  sh.getRange('B1').setNumberFormat('@').setValue(iso);
  sh.getRange('B2').setValue(new Date());
}

/* Ticking Picked sinks the row to the bottom of its tab, so the top of each
   bench is always just the builds nobody has ruled on yet.

   This has to be an INSTALLABLE trigger. A simple onEdit() only runs in a
   script bound to the sheet, and this one is standalone (see book_()), so
   nothing would ever fire. Installed once by setUpTabs, and re-running that
   will not add a second one. */
function installEditTrigger_() {
  var already = ScriptApp.getProjectTriggers().some(function (t) {
    return t.getHandlerFunction() === 'onLabEdit';
  });
  if (already) return;
  ScriptApp.newTrigger('onLabEdit').forSpreadsheet(book_().getId()).onEdit().create();
}

function onLabEdit(e) {
  try {
    var sh = e.range.getSheet();
    var mine = Object.keys(TABS).map(function (k) { return TABS[k]; });
    if (mine.indexOf(sh.getName()) === -1) return;

    var row = e.range.getRow();
    if (row < 2) return;
    var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    var col = head.indexOf(PICKED) + 1;
    if (!col || e.range.getColumn() !== col) return;
    if (sh.getRange(row, col).getValue() !== true) return;   // unticking leaves it put

    var last = sh.getLastRow();
    if (row >= last) return;
    sh.moveRows(sh.getRange(row + ':' + row), last + 1);
  } catch (err) {
    // An edit handler that throws shows the editor a red banner on an
    // unrelated keystroke. Log it and let them get on with it.
    console.log('[labs] onLabEdit: ' + err);
  }
}
