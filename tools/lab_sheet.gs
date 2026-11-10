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
 *  2. Project Settings > Script properties, add two:
 *       LAB_EXPORT_URL   https://<project>.supabase.co/functions/v1/lab-export
 *       LAB_EXPORT_KEY   the same string you set as LAB_EXPORT_KEY in Supabase
 *     They go here rather than in the code so the key is not in the file, and
 *     not in anyone's screenshot of it.
 *  3. Run `pullLabs` once by hand and approve the permission prompt.
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

// Written by people, never by this script. They sit to the right of the build
// columns, and a new question on a bench is inserted before them so that a
// note never ends up against the wrong row.
var MINE = ['Picked', 'Picked by', 'Ran (month)', 'Notes'];
var FIRST = ['Date', 'Called', 'Built by'];
var SYNC = 'Sync';

function pullLabs() {
  var props = PropertiesService.getScriptProperties();
  var url = props.getProperty('LAB_EXPORT_URL');
  var key = props.getProperty('LAB_EXPORT_KEY');
  if (!url || !key) throw new Error('Set LAB_EXPORT_URL and LAB_EXPORT_KEY in Script properties.');

  var book = SpreadsheetApp.getActiveSpreadsheet();
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

  sh.getRange(sh.getLastRow() + 1, 1, rows.length, head.length).setValues(rows);
  sh.getRange(2, head.indexOf('Date') + 1, sh.getLastRow() - 1, 1)
    .setNumberFormat('ddd d mmm yyyy');
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
