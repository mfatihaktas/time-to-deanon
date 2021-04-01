import simpy

from debug_utils import *

class SenderProbe():
	def __init__(self, _id, env, inter_tx_time, tx_dur, num_packets, deanoner):
		self._id = _id
		self.env = env
		self.inter_tx_time = inter_tx_time
		self.tx_dur = tx_dur
		self.num_packets = num_packets
		self.deanoner = deanoner

	def __repr__(self):
		return "SenderProbe[id= {}, inter_tx_time= {}, tx_dur= {}, num_packets= {}]".format(self._id, self.inter_tx_time, self.tx_dur, self.num_packets)

	def run(self):
		while True:
			yield self.env.timeout(self.inter_tx_time)

			self.deanoner.put(
				{
					'src_id': self._id,
					'event': 'tx',
					'dur': self.tx_dur,
					'num_packets': self.num_packets
				}
			)

class TrueRecverProbe():
	def __init__(self, _id, env, mu, deanoner):
		self.env = env
		self.mu = mu
		self.deanoner = deanoner

		self.X = Exp(mu)

		self.store = simpy.Store(env)
		self.action = self.env.process(self.run())

	def __repr__(self):
		return "TrueRecverProbe[id= {}, mu= {}]".format(self._id, self.mu)

	def put(self):
		slog(DEBUG, self.env, self, "recved", m)
		self.store.put(m)

	def run(self):
		while True:
			m = yield self.store.get()
			check(m['cmd'] == 'probe', "Cmd should have been probe.")

			dur, least_num_rx = m['dur'], m['least_num_rx']
			# TODO: the following sampling is not efficient
			inter_rx_time_l = []
			t = 0
			while len(inter_rx_time_l) < least_num_rx:
				while True:
					x = self.X.sample()
					if t + x < dur:
						t = t + x
						inter_rx_time_l.append(x)

			for x in inter_rx_time_l:
				yield self.env.timeout(x)

				self.deanoner.put(
					{
						'id': self._id,
						'event': 'rx',
						'time': self.env.now
					}
				)

class RecverProbe():
	def __init__(self, _id, env, mu, deanoner):
		self.env = env
		self.mu = mu
		self.deanoner = deanoner

		self.X = Exp(mu)

		self.store = simpy.Store(env)

	def __repr__(self):
		return "RecverProbe[id= {}, mu= {}]".format(self._id, self.mu)

	def put(self):
		slog(DEBUG, self.env, self, "recved", m)
		self.store.put(m)

	def run(self):
		while True:
			m = yield self.store.get()
			check(m['cmd'] == 'probe', "'cmd' should have been equal to 'probe'.")

			end_time = self.env.now + m['dur']
			while end_time < self.env.now:
				yield self.env.timeout(self.X.sample())

				self.deanoner.put(
					{
						'id': self._id,
						'event': 'rx',
						'time': self.env.now
					}
				)

class DeAnoner():
	def __init__(self, _id, true_recver_probe, false_recver_probe_l):
		self._id = _id
		self.true_recver_probe = true_recver_probe
		self.false_recver_probe_l = false_recver_probe_l

		self.store = simpy.Store(env)

		self.suspect_id_s = set([true_recver_probe._id] + [p._id for p in false_recver_probe_l])
		self.id__num_rxed_m = {}
		self.num_packets_txed = 0
		self.attack_dur = 0

		self.num_attack_wins = 0
		self.deanond_finish_time = None

	def __repr__(self):
		return "DeAnoner[id= {}]".format(self._id)

	def put(self, m):
		slog(DEBUG, self.env, self, "recved", m)
		self.store.put(m)

	def run(self):
		while True:
			m = yield self.store.get()

			if m['event'] == 'tx':
				self.num_packets_txed = m['num_packets']
				self.attack_dur = m['dur']

				if self.true_recver_probe._id in self.suspect_id_s:
					self.true_recver_probe.put(
						{
							'cmd': 'probe',
							'dur': self.attack_dur,
							'least_num_rx': self.num_packets_txed
						}
					)

				for rp in self.false_recver_probe_l:
					if rp._id in self.suspect_id_s:
						rp.put(
							{
								'cmd': 'probe',
								'dur': self.attack_dur
							}
						)
			elif m['event'] == 'rx' and self.num_packets_txed > 0:
				i = m['id']

				self.id__num_rxed_m[i] = {}

				self.suspect_id_s


def sim():

	TrueRecverProbe('tr', self.env, mu, dur, least_num_rx, out)
