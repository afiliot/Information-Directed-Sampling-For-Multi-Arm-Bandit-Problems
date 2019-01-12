# File containing different experiments that we can run

# Importation
import numpy as np
from MAB import GenericMAB
from BernoulliMAB import BetaBernoulliMAB
from GaussianMAB import GaussianMAB
from FiniteSetsMAB import FiniteSets
from LinMAB import *
import matplotlib.pyplot as plt
from scipy.stats import norm
from tqdm import tqdm
import inspect


param = {
    'UCB1': {'rho': 0.2},
    'BayesUCB': {'p1': 1, 'p2': 1, 'c':0},
    'MOSS': {'rho': 0.2},
    'ExploreCommit': {'m': 50},
    'IDS_approx': {'N_steps': 10000, 'display_results': False},
    'Tuned_GPUCB': {'c': 0.9},
}

def plotRegret(methods, mean_regret, title):
    for i in range(len(methods)):
        plt.plot(mean_regret[i], label=methods[i])
    plt.title(title)
    plt.ylabel('Cumulative regret')
    plt.xlabel('Time period')
    plt.legend()
    plt.show()


def beta_bernoulli_expe(n_expe, n_arms, T, methods, param_dic, doplot=True):
    all_regrets = np.zeros((len(methods), n_expe, T))
    for j in tqdm(range(n_expe)):
        p = np.random.uniform(size=n_arms)
        my_mab = BetaBernoulliMAB(p)
        for i, m in enumerate(methods):
            alg = my_mab.__getattribute__(m)
            args = inspect.getfullargspec(alg)[0][2:]
            args = [T]+[param_dic[m][i] for i in args]
            all_regrets[i, j] = my_mab.regret(alg(*args)[0], T)
    mean_regret = all_regrets.mean(axis=1)
    if doplot:
        plotRegret(methods, mean_regret, 'Binary rewards')
    return mean_regret


def build_finite(L, K, N):
    """
    Building automatically a finite bandit environment
    :param L: Number of possible values for theta
    :param K: Number of arms
    :param N: Number of possible rewards
    :return: Parameters required for launching an experiment with a finite bandit (prior, q values and R function)
    """
    R = np.linspace(0., 1., N)
    q = np.random.uniform(size=(L, K, N))
    for i in range(q.shape[0]):
        q[i] = np.apply_along_axis(lambda x: x / x.sum(), 1, q[i])
        # For a given theta and a given arm, the sum over the reward should be one
    p = np.random.uniform(0, 1, L)  # In case of a random prior
    p = p / p.sum()
    return p, q, R


def build_finite_deterministic():
    """
    Building a given finite MAB with 2 possible values for theta, 5 arms and eleven different rewards
    :return: Parameters required for launching an experiment with a finite bandit (prior, q values and R function)
    """
    R = np.linspace(0., 1., 11)
    q = np.random.uniform(size=(2, 5, 11))
    for i in range(q.shape[0]):
        q[i] = np.apply_along_axis(lambda x: x / x.sum(), 1, q[i])
    p = np.array([0.35, 0.65])
    return p, q, R


def check_finite(prior, q, R, theta, N, T):
    nb_arms = q.shape[1]
    nb_rewards = q.shape[2]
    method = ['F'] * nb_arms
    param = [[np.arange(nb_rewards), q[theta, i, :]] for i in range(nb_arms)]
    my_MAB = FiniteSets(method, param, q, prior, R)
    param2 = [[R, q[theta, i, :]] for i in range(q.shape[1])]
    check_MAB = GenericMAB(method, param2)
    regret_IDS = my_MAB.MC_regret(method='IDS', N=N, T=T)
    plt.plot(regret_IDS, label='IDS')
    plt.plot(check_MAB.MC_regret(method='UCB1', N=N, T=T, param=0.2), label='UCB1')
    plt.plot(check_MAB.MC_regret(method='TS', N=N, T=T), label='TS')
    plt.ylabel('Cumulative Regret')
    plt.xlabel('Rounds')
    plt.legend()
    plt.show()


##### Gaussian test ######

def check_gaussian(n_expe, n_arms, T, doplot=True):
    methods = ['UCB1', 'IDS_approx','Tuned_GPUCB', 'BayesUCB', 'GPUCB', 'KG', 'KG_star']  #
    all_regrets = np.zeros((len(methods), n_expe, T))
    for j in tqdm(range(n_expe)):
        mu, sigma, p = np.random.normal(0, 1, n_arms), np.ones(n_arms), []
        for i in range(len(mu)):
            p.append([mu[i], sigma[i]])
        my_mab = GaussianMAB(p)
        for i, m in enumerate(methods):
            alg = my_mab.__getattribute__(m)
            args = inspect.getfullargspec(alg)[0][2:]
            args = [T]+[param[m][i] for i in args]
            all_regrets[i, j] = my_mab.regret(alg(*args)[0], T)
    mean_regret = all_regrets.mean(axis=1)
    if doplot:
        plotRegret(methods, mean_regret, 'Gaussian rewards')
    return mean_regret


def LinearGaussianMAB(n_expe, n_features, n_arms, T, doplot=True, plotMAB=False):
    methods = ['LinUCB', 'Tuned_GPUCB', 'GPUCB', 'TS', 'BayesUCB', 'IDS']
    u = 1 / np.sqrt(5)
    regret = np.zeros((len(methods), n_expe, T))
    for n in tqdm(range(n_expe)):
        random_state = np.random.randint(0, 312414)
        model = PaperLinModel(u, n_features, n_arms, sigma=10, random_state=random_state)
        if plotMAB:
            model.rewards_plot()
        lMAB = LinMAB(model)
        for i, m in enumerate(methods):
            alg = lMAB.__getattribute__(m)
            reward, arm_sequence = alg(T)
            regret[i, n, :] = model.best_arm_reward() - reward
    mean_regret = [np.array([np.mean(regret[i, :, t]) for t in range(T)]).cumsum() for i in range(len(methods))]
    if doplot:
        plotRegret(methods, mean_regret, 'Linear-Gaussian Model')
    return mean_regret

