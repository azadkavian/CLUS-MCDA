from sklearn.cluster import KMeans
from matplotlib import pyplot
from scipy.spatial import ConvexHull
import util.readData as dataProvider
import numpy as np
import math

businessAreas = dataProvider.getBusinessAreasList()
k = 5 # default number of clusters
sample_case_study = 'Contractor'
min_columns = [0 , 5 , 6]
max_columns = [1, 2, 3, 4]
suppliersData = {}
kMeans = KMeans(n_clusters=k)

def plotUnitsPerBusinessAreas(suppliersData):
    plot_handles = []
    for area in suppliersData:
        ds = [item for item in suppliersData[area].values()]
        X = [item[0] for item in ds]
        Y = [item[1] for item in ds]
        plot, = pyplot.plot(X,Y,'o', label=area)
        plot_handles.append(plot)

    #pyplot.legend(handles=plot_handles, bbox_to_anchor=(1.05, 2.5), loc=2, borderaxespad=0.)
    pyplot.show()
    return None

def __initClustering(clusters):
    """
    """
    suppliersData = {}
    for area in businessAreas.values():
        suppliersData[area] = dataProvider.getSuppliersData(area)
    
    k = clusters
    kMeans = KMeans(n_clusters=k)
    
    mustBeInClustering = {}
    for area in businessAreas.values():
        mustBeInClustering[area] = True

    return suppliersData, k, kMeans, mustBeInClustering


def __isClusteringNeeded(mustBeInClustering):
    """
    """
    for area in businessAreas.values():
        if mustBeInClustering[area]:
            return True

    return False


def runKMeansForAllAreas(suppliersData, k, kMeans, mustBeInClustering):
    """
    """
    clusters = {}
    for area in businessAreas.values():
        if mustBeInClustering[area] == False:
            continue # ready for ranking

        data = []
        for item in suppliersData[area]:
            costPerPrice = suppliersData[area][item][0]
            data.append(np.array([item, costPerPrice]))

        if len(data) <= 5: # no clustering needed
            mustBeInClustering[area] = False
            clusters[area] = {'FinalCandidates': np.array(data)}
            continue

        data = np.array(data)
        kMeans = KMeans(n_clusters=k)
        kMeans.fit(data)
        labels = kMeans.labels_
        centroids = kMeans.cluster_centers_

        plot_handles = []
        clusterData = {}
        for i in range(k):
            clusterLabel = 'Cluster{}'.format(i + 1)
            # select only data observations with cluster label == i
            ds = data[np.where(labels==i)]
            clusterData[clusterLabel] = ds[:, :2]
            # plot the data observations
            # plot, = pyplot.plot(ds[:,0],ds[:,1],'o', label=clusterLabel)
            # plot_handles.append(plot)
            # # plot the centroids
            # lines = pyplot.plot(centroids[i,0],centroids[i,1],'kx')
            # make the centroid x's bigger
            # pyplot.setp(lines,ms=15.0)
            # pyplot.setp(lines,mew=2.0)

            # points = np.array([np.array([row[0], row[1]]) for row in ds])
            # if points.shape[0] < 3:
            #     continue
            # hull = ConvexHull(points)
            # for simplex in hull.simplices:
            #     pyplot.plot(points[simplex, 0], points[simplex, 1], 'k-')
            
            # pyplot.plot(points[hull.vertices,0], points[hull.vertices,1], 'r--', lw=2)
            # pyplot.plot(points[hull.vertices[0],0], points[hull.vertices[0],1], 'ro')

        clusters[area] = clusterData
        # pyplot.legend(handles=plot_handles, bbox_to_anchor=(1.05, 2.5), loc=2, borderaxespad=0.)
        # pyplot.show()
        

    return clusters, mustBeInClustering

def runCLUSMCDA(k_clusters=5):
    """
    """
    suppliersData, k, kMeans, mustBeInClustering = __initClustering(k_clusters)

    cycle = 0
    while __isClusteringNeeded(mustBeInClustering):
        cycle += 1
        print(cycle, mustBeInClustering.values(), '\n')
        clusters, mustBeInClustering = runKMeansForAllAreas(suppliersData, k, kMeans, mustBeInClustering)
        # if cycle > 1:
        #     print(clusters)
        rowsToBeRemoved = []
        for area in businessAreas.values():
            if not mustBeInClustering[area]:
                continue

            areaClusterData = []
            for cluster in clusters[area]:
                areaClusterRows = clusters[area][cluster][:,0]

                x = np.array([dataProvider.getRow(row) for row in areaClusterRows])
                w = [0.207317073, 0.12195122, 0.170731707, 0.12195122, 0.097560976, 0.146341463, 0.134146341]
                n = len(w) # number of columns

                # normalizing X
                X = []
                for i in range(len(x)):
                    row = []
                    for j in range(len(x[i])):
                        RoSoS = 0.0 # Root of Sum of Squares
                        for k in range(len(x)):
                            RoSoS += float(x[k][j]) ** 2
                        RoSoS = float(math.sqrt(RoSoS))
                        if RoSoS == 0.0:
                            RoSoS = 0.00000001 # a tiny number
                        row.append(float(x[i][j]) / RoSoS)
                    X.append(np.array(row))
                        
                X = np.array(X)

                # calculating Y
                Y = []
                for i in range(len(X)):
                    Yjg = 0
                    for g in max_columns:
                        Yjg += w[g] * X[i][g]

                    Ygn = 0
                    for ng in min_columns:
                        Ygn += w[ng] * X[i][ng]

                    Yi = Yjg - Ygn
                    Y.append(Yi)

                Y = np.array(Y)

                # calculating R
                R = []
                for j in range(n):
                    rj = X[0][j]
                    if j in min_columns:
                        for i in range(len(X)):
                            if rj > X[i][j]:
                                rj = X[i][j]

                    else:
                        for i in range(len(X)):
                            if rj < X[i][j]:
                                rj = X[i][j]

                    R.append(rj)

                R = np.array(R)

                # calculating Z
                Z = []
                for i in range(len(X)):
                    zi = X[i][0]
                    for j in range(n):
                        exp = abs(w[j] * R[j] - w[j] * X[i][j])
                        if zi < exp:
                            zi = exp

                    Z.append(zi)

                Z = np.array(Z)
                
                # calculating U
                U = []
                for i in range(len(X)):
                    up = 1
                    for g in max_columns:
                        up *= X[i][j] ** w[j]

                    bot = 1
                    for ng in min_columns:
                        bot *= X[i][j] ** w[j]

                    if bot == 0.0:
                        bot == 0.0000001 # a tiny number
                    ui = up / bot
                    U.append(ui)

                U = np.array(U)
                
                if cluster == 'FinalCandidates':
                    candidates = len(U)
                    for i in range(candidates):
                        areaClusterData.append(np.array(['Candidate{}'.format(i + 1), Y[i], Z[i], U[i]]))

                else:
                    # gettting means
                    y = 0
                    z = 0
                    u = 0
                    no = len(Z)
                    for i in range(no):
                        y += Y[i]
                        z += Z[i]
                        u += U[i]
                    y /= no
                    z /= no
                    u /= no

                    areaClusterData.append(np.array([cluster, float(y), float(z), float(u)]))

            areaClusterData = np.array(areaClusterData)

            # determining rankings for each column
            yRanks = getRanks(areaClusterData[:,1])
            zRanks = getRanks(areaClusterData[:,2], descending=True)
            uRanks = getRanks(areaClusterData[:,3])

            fRanks = getFinalRanks(yRanks, zRanks, uRanks)
            # appending ranks to data rows
            ranks = np.array([[yRanks[i], zRanks[i], uRanks[i], fRanks[i]] for i in range(len(yRanks))])
            
            areaClusterDataRanks = []
            for i in range(len(ranks)):
                oldRow = areaClusterData[i]
                newRow = np.insert(oldRow, len(oldRow), ranks[i])
                areaClusterDataRanks.append(newRow)

            areaClusterDataRanks = np.array(areaClusterDataRanks)

            # finding top 3 clusters/candidates
            topClusters = [row[0] for row in areaClusterDataRanks if int(row[-1]) <= 3]
            topClusters = {}
            lowClusters = []
            for row in areaClusterDataRanks:
                rank = int(row[-1])
                if rank <= 3:
                    topClusters[rank] = row[0]
                else:
                    lowClusters.append(row[0])

            # removing low clusters from data set
            for cluster in lowClusters:
                rowsToBeRemoved.extend(clusters[area][cluster][:,0].astype(int).tolist())

        rowsToBeRemoved.sort()
        dataLength = 0
        for area in suppliersData:
            dataLength += len(suppliersData[area])
        print('old length:', dataLength)
        print('to be removed', len(rowsToBeRemoved))
        for area in suppliersData:
            for uselessRow in rowsToBeRemoved:
                suppliersData[area].pop(uselessRow, None)
        dataLength = 0
        for area in suppliersData:
            dataLength += len(suppliersData[area])
        print('new length:', dataLength, '\n\n')

def getRanks(dataColumn, descending=False):
    """
    """
    items = [item for item in dataColumn]
    itemsSorted = [item for item in dataColumn]
    itemsSorted.sort(reverse=descending)

    ranks = [itemsSorted.index(item) + 1 for item in items]

    return ranks


def getFinalRanks(yRanks, zRanks, uRanks):
    """
    """
    rankTuples = []
    data = []
    for i in range(len(yRanks)):
        row = [yRanks[i], zRanks[i], uRanks[i]]
        row.sort()
        rankTuples.append(row)
        data.append(row)

    rankTuples.sort()
    fRanks = [rankTuples.index(row) + 1 for row in data]
    return fRanks

if __name__ == '__main__':
    runCLUSMCDA()