"""Single-coordinator, persistent confidentiality labels for mediated handoffs."""
import json
from pathlib import Path
import threading


class FlowPolicy:
    def __init__(self, path, clearances, resources, *, on_stop):
        self.path, self.on_stop = Path(path), on_stop
        self.lock = threading.RLock()
        if any(isinstance(labels, str) for section in (clearances, resources) for labels in section.values()):
            raise ValueError('Label collections cannot be a single string')
        policy = {'clearances': {name: sorted(set(labels)) for name, labels in clearances.items()},
                  'resources': {name: sorted(set(labels)) for name, labels in resources.items()}}
        if any(not isinstance(name, str) or not name or any(not isinstance(label, str) or not label for label in labels)
               for section in policy.values() for name, labels in section.items()):
            raise ValueError('Use explicit nonempty identities and label strings')
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state['policy'] != policy:
                raise ValueError('An existing label ledger cannot silently change policy')
            if any(item.get('stage') == 'commit_prepared' for item in self.state['transfers']):
                self.state['stopped'] = True
                self._save()
        else:
            self.state = {'policy': policy, 'labels': {name: [] for name in clearances},
                          'exposures': [], 'transfers': [], 'stopped': False}
            self._save()
        if self.state['stopped']:
            self.on_stop()

    def _save(self):
        temporary = self.path.with_name(self.path.name + '.tmp')
        temporary.write_text(json.dumps(self.state, indent=2) + '\n')
        temporary.replace(self.path)

    def begin_session(self, identity_session):
        """An uncleared predecessor marker makes resumption fail closed."""
        with self.lock:
            if self.state.get('active_session') is not None:
                self.state['stopped'] = True
            if not self.state['stopped']:
                self.state['active_session'] = identity_session
            self._save()
            stopped = self.state['stopped']
        if stopped:
            self.on_stop()

    def bind_conversation(self, conversation):
        with self.lock:
            previous = self.state.get('provider_conversation')
            if previous is not None and previous != conversation:
                raise PermissionError('Identity ledger belongs to another conversation')
            self.state['provider_conversation'] = conversation
            self._save()

    def end_session(self, identity_session):
        with self.lock:
            if self.state['stopped'] or self.state.get('active_session') != identity_session:
                raise PermissionError('Identity session cannot close cleanly')
            self.state['active_session'] = None
            self._save()

    def expose(self, subject, resource, digest):
        """Persist possible exposure BEFORE the broker commits bytes.

        The trusted host maps kernel principals to these stable subject IDs.
        A subsequent failed commit can over-label the subject; labels never fall.
        """
        with self.lock:
            if self.state['stopped']:
                raise PermissionError('Information-flow scope stopped')
            labels = set(self.state['policy']['resources'][resource])
            clearance = set(self.state['policy']['clearances'][subject])
            if not labels <= clearance:
                raise PermissionError('Subject lacks resource clearance')
            self.state['labels'][subject] = sorted(set(self.state['labels'][subject]) | labels)
            self.state['exposures'].append({'subject': subject, 'resource_id': resource,
                                            'resource_sha256': digest, 'labels': sorted(labels),
                                            'stage': 'before_byte_commit'})
            self._save()

    def context(self, sender, recipient):
        with self.lock:
            labels = set(self.state['labels'][sender])
            clearance = set(self.state['policy']['clearances'][recipient])
            return {'sender': sender, 'recipient': recipient, 'sender_labels': sorted(labels),
                    'recipient_clearance': sorted(clearance), 'scope_stopped': self.state['stopped'],
                    'permitted': not self.state['stopped'] and labels <= clearance,
                    'scope': 'Trusted confidentiality metadata, not proof of intent. All sender output inherits possible exposure labels; no semantic declassification.'}

    def exposure_context(self, subject):
        with self.lock:
            return {'subject': subject, 'possible_exposure_labels': list(self.state['labels'][subject]),
                    'clearance': list(self.state['policy']['clearances'][subject]),
                    'scope_stopped': self.state['stopped']}

    def stop(self):
        try:
            with self.lock:
                self.state['stopped'] = True
                self._save()
        finally:
            self.on_stop()

    def transfer(self, sender, recipient, publish):
        must_stop = False
        try:
            with self.lock:
                decision = self.context(sender, recipient)
                if not decision['permitted']:
                    decision.update(delivered=False, reason='scope_stopped' if self.state['stopped'] else 'recipient_clearance')
                    self.state['stopped'] = True
                    must_stop = True
                    self.state['transfers'].append(decision)
                    self._save()
                    return decision
                # Preserve recipient labels before publishing any bytes. This
                # deliberately over-approximates exposure if publication fails.
                self.state['labels'][recipient] = sorted(set(self.state['labels'][recipient]) | set(decision['sender_labels']))
                decision.update(delivered=True, recipient_labels=self.state['labels'][recipient], stage='commit_prepared')
                self.state['transfers'].append(decision)
                self._save()
                publish(dict(decision))
                decision['stage'] = 'committed'
                self._save()
                return decision
        except Exception:
            must_stop = True
            with self.lock:
                self.state['stopped'] = True
                self._save()
            raise
        finally:
            # No flow lock is held when taking a broker/revocation lock.
            if must_stop:
                self.on_stop()
