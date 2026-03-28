# Monthly ROI Report

## Overview

`roi_report_generator.py` is the most important retention asset in the Genesis AI Systems stack. It converts automation activity into business language the client understands: time saved, leads handled, and revenue influenced.

This enhancement is included in all retainers because it is one of the strongest anti-churn tools you can have.

## Core Promise

Every month, the client receives a document that answers:

- What did the AI do for me?
- How much time did it save?
- How much revenue did it likely influence?
- Why should I keep paying for this?

## Inputs

- Google Sheets lead logs
- optional Vapi monthly metrics JSON
- optional email activity JSON
- uptime logs
- average deal value

## Outputs

- PDF report
- email delivery to the client
- Google Drive archived copy

## Schedule

- run on the `1st of every month`
- import `roi_report_n8n.json` for no-code scheduling
