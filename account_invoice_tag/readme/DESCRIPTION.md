This module adds a tagging system to customer and vendor invoices (`account.move`).

Tags can be created and managed from **Accounting > Configuration > Invoice Tags**
(restricted to account managers). Each tag has a name and a configurable color.
Tags can also be marked as **deprecated** to prevent them from being assigned to
new invoices while keeping them visible on existing ones.

On invoices and credit notes (both customer and vendor), tags are displayed next
to the journal field in the form header and are editable only while the invoice
is in draft state. Tags are also shown as colored badges in the invoice list view.

The invoice search view includes a **With Tags** filter and a **Tags** group-by
option to help locate and organize invoices by their tags.

When exporting invoices, the Tags column is rendered as a single comma-separated
string (e.g. ``Urgent, Pending``) instead of expanding into multiple rows, making
the exported file easier to process.